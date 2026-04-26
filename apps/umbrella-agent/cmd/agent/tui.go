package main

import (
	"crypto/tls"
	"fmt"
	"net/http"
	"os"
	"strings"
	"time"

	"golang.org/x/term"

	"github.com/flow-ecosystem/umbrella-agent/internal/agent"
	"github.com/flow-ecosystem/umbrella-agent/internal/api"
	"github.com/flow-ecosystem/umbrella-agent/internal/config"
	"github.com/flow-ecosystem/umbrella-agent/internal/enforce"
	"github.com/flow-ecosystem/umbrella-agent/internal/state"
)

// ── ANSI helpers ──────────────────────────────────────────

const (
	aReset  = "\033[0m"
	aBold   = "\033[1m"
	aDim    = "\033[2m"
	aRed    = "\033[31m"
	aGreen  = "\033[32m"
	aYellow = "\033[33m"
	aCyan   = "\033[36m"
)

func ac(code, s string) string { return code + s + aReset }

// visLen returns visible rune count, stripping ANSI escape sequences.
func visLen(s string) int {
	n, esc := 0, false
	for _, r := range s {
		switch {
		case r == '\x1b':
			esc = true
		case esc:
			if r == 'm' {
				esc = false
			}
		default:
			n++
		}
	}
	return n
}

// boxLine pads content to innerWidth visible chars and wraps it in ║…║.
func boxLine(content string, innerWidth int) string {
	pad := innerWidth - visLen(content)
	if pad < 0 {
		pad = 0
	}
	return "  ║" + content + strings.Repeat(" ", pad) + "║"
}

// ── Key reader ────────────────────────────────────────────

const (
	kEnter = "enter"
	kCtrlC = "\x03"
)

func startKeys() <-chan string {
	ch := make(chan string, 16)
	go func() {
		buf := make([]byte, 6)
		for {
			n, _ := os.Stdin.Read(buf)
			if n == 0 {
				continue
			}
			b := buf[:n]
			for i := 0; i < n; i++ {
				switch b[i] {
				case 0x0d, 0x0a:
					ch <- kEnter
				default:
					ch <- string([]byte{b[i]})
				}
			}
		}
	}()
	return ch
}

// ── TUI globals ───────────────────────────────────────────

var (
	tuiFD    int
	tuiOldSt *term.State
)

func tuiRaw() {
	old, err := term.MakeRaw(tuiFD)
	if err != nil {
		fatalf("raw mode: %v", err)
	}
	tuiOldSt = old
	fmt.Print("\033[?25l")
}

func tuiRestore() {
	if tuiOldSt != nil {
		term.Restore(tuiFD, tuiOldSt)
	}
	fmt.Print("\033[?25h\033[2J\033[H")
}

// ── runTUI ────────────────────────────────────────────────

func runTUI(cfgFile string) {
	tuiFD = int(os.Stdin.Fd())
	if !term.IsTerminal(tuiFD) {
		doSetup(cfgFile)
		return
	}
	enableANSI()
	tuiRaw()
	defer tuiRestore()

	keys := startKeys()
	cfg, _ := config.Load(cfgFile)
	s, _ := state.Load(cfg.StateFile)

	showWelcome(keys, cfg.AgentVersion)

	if !s.IsEnrolled() {
		var ok bool
		cfgFile, ok = firstRunSetup(cfgFile, keys)
		if !ok {
			return
		}
		cfg, _ = config.Load(cfgFile)
		s, _ = state.Load(cfg.StateFile)
		verifyScreen(cfg, s, keys)
		finalInstallScreen(cfgFile, cfg, s, keys)
	} else {
		verifyScreen(cfg, s, keys)
		svcSt, _ := serviceStatus()
		if svcSt != "active" && svcSt != "running" {
			serviceInstallPrompt(cfgFile, keys)
		}
	}

	// Main loop: monitor ↔ logs ↔ policies.
	for {
		next := tuiMonitor(cfgFile, keys)
		cfg2, _ := config.Load(cfgFile)
		switch next {
		case "quit":
			return
		case "logs":
			if !tuiLogs(cfg2.LogFile, keys) {
				return
			}
		case "policies":
			if !tuiPolicies(cfg2.StateFile, keys) {
				return
			}
		}
	}
}

// ── Welcome screen ────────────────────────────────────────

func showWelcome(keys <-chan string, version string) {
	const inner = 43
	top := "  ╔" + strings.Repeat("═", inner) + "╗"
	bot := "  ╚" + strings.Repeat("═", inner) + "╝"
	empty := boxLine("", inner)

	fmt.Print("\033[2J\033[H")
	fmt.Println(top)
	fmt.Println(empty)
	fmt.Println(boxLine(`        /‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾\`, inner))
	fmt.Println(boxLine(`       /    ████  █████      \`, inner))
	fmt.Println(boxLine(`      /     █  █  █   █       \`, inner))
	fmt.Println(boxLine(`      \     ████  █████       /`, inner))
	fmt.Println(boxLine(`       \    █  █  █  ██      /`, inner))
	fmt.Println(boxLine(`        \   ████  █   ██    /`, inner))
	fmt.Println(boxLine(`         ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾`, inner))
	fmt.Println(empty)
	fmt.Println(boxLine("        "+ac(aBold+aCyan, "U M B R E L L A"), inner))
	fmt.Println(boxLine("            "+ac(aBold+aCyan, "A G E N T"), inner))
	fmt.Println(boxLine("    Security Endpoint Management", inner))
	fmt.Println(boxLine("              "+ac(aDim, "v"+version), inner))
	fmt.Println(empty)
	fmt.Println(bot)
	fmt.Printf("\n       %s\n", ac(aDim, "Нажмите любую клавишу..."))

	select {
	case <-time.After(2 * time.Second):
	case <-keys:
	}
}

// ── Raw-mode text input ───────────────────────────────────

const maxInputLen = 256

func rawInput(keys <-chan string, mask bool, initial string) (string, bool) {
	buf := []byte(initial)
	fmt.Print("\033[?25h")

	redraw := func() {
		disp := string(buf)
		if mask {
			disp = strings.Repeat("*", len(buf))
		}
		fmt.Printf("\r  > %s\033[K", disp)
	}
	redraw()

	for {
		k := <-keys
		switch k {
		case kEnter:
			fmt.Println()
			fmt.Print("\033[?25l")
			return string(buf), true
		case kCtrlC:
			fmt.Println()
			fmt.Print("\033[?25l")
			return "", false
		case "\x7f", "\x08":
			if len(buf) > 0 {
				buf = buf[:len(buf)-1]
				redraw()
			}
		default:
			if len(k) == 1 && k[0] >= 0x20 && k[0] <= 0x7e && len(buf) < maxInputLen {
				buf = append(buf, k[0])
				redraw()
			}
		}
	}
}

// ── Wizard step helpers ───────────────────────────────────

const wizardW = 52

func wizardSep() string { return "  " + strings.Repeat("─", wizardW) }

func wizardInputStep(keys <-chan string, title, step, label, hint string, mask bool, initial string) (string, bool) {
	sep := wizardSep()
	fmt.Print("\033[2J\033[H")
	fmt.Printf("  %-44s%s\n", ac(aBold+aCyan, title), ac(aDim, step))
	fmt.Println(sep)
	fmt.Println()
	fmt.Printf("  %s\n", label)
	if hint != "" {
		fmt.Printf("  %s\n", ac(aDim, hint))
	} else {
		fmt.Println()
	}
	fmt.Println()
	fmt.Println()
	fmt.Println()
	fmt.Println(sep)
	fmt.Printf("  %s\n", ac(aDim, "Enter — далее   Ctrl+C — отмена"))
	fmt.Print("\033[4A")

	return rawInput(keys, mask, initial)
}

func wizardYesNoStep(keys <-chan string, title, step, question, description string) (bool, bool) {
	sep := wizardSep()
	fmt.Print("\033[2J\033[H")
	fmt.Printf("  %-44s%s\n", ac(aBold+aCyan, title), ac(aDim, step))
	fmt.Println(sep)
	fmt.Println()
	fmt.Printf("  %s\n", question)
	if description != "" {
		fmt.Println()
		fmt.Printf("  %s\n", ac(aDim, description))
	}
	fmt.Println()
	fmt.Printf("  %s\n", ac(aDim, "[ y ] Да   [ N ] Нет (по умолчанию)"))
	fmt.Println()
	fmt.Println(sep)
	fmt.Printf("  %s\n", ac(aDim, "Ctrl+C — отмена"))

	for {
		k := <-keys
		switch k {
		case "y", "Y":
			return true, true
		case "n", "N", kEnter:
			return false, true
		case kCtrlC:
			return false, false
		}
	}
}

// ── Enrollment step ───────────────────────────────────────

func enrollStep(keys <-chan string, cfg *config.Config, s *state.State, cfgFile string) (string, error) {
	sep := wizardSep()
	fmt.Print("\033[2J\033[H")
	fmt.Printf("  %-44s%s\n", ac(aBold+aCyan, "НАСТРОЙКА АГЕНТА"), ac(aDim, "Регистрация"))
	fmt.Println(sep)
	fmt.Println()
	fmt.Printf("  Подключение к %s\n\n", ac(aCyan, cfg.ServerURL))

	type res struct{ err error }
	ch := make(chan res, 1)
	go func() {
		a := agent.New(*cfg, s)
		ch <- res{a.Enroll()}
	}()

	spin := []string{"⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"}
	tick := time.NewTicker(80 * time.Millisecond)
	frame := 0
	var enrollErr error
loop:
	for {
		select {
		case <-tick.C:
			fmt.Printf("\r  %s  регистрация...\033[K", spin[frame%len(spin)])
			frame++
		case r := <-ch:
			tick.Stop()
			fmt.Printf("\r\033[K")
			enrollErr = r.err
			break loop
		}
	}

	if enrollErr != nil {
		fmt.Printf("  %s  Ошибка:\n\n", ac(aRed, "✗"))
		msg := enrollErr.Error()
		for len(msg) > 0 {
			chunk := msg
			if len(chunk) > wizardW-4 {
				chunk = chunk[:wizardW-4]
			}
			fmt.Printf("     %s\n", chunk)
			msg = msg[len(chunk):]
		}
		fmt.Println()
		fmt.Println(sep)
		fmt.Printf("  %s\n", ac(aDim, "[ r ] Повторить   [ q ] Выйти"))
		return "", enrollErr
	}

	fmt.Printf("  %s  Регистрация успешна\n", ac(aGreen, "✓"))
	fmt.Printf("     ID агента: %s\n", ac(aCyan, s.AgentID))

	out := writeConfig(cfg, cfgFile)
	if out != "" {
		fmt.Printf("  %s  Конфиг сохранён: %s\n", ac(aGreen, "✓"), ac(aDim, out))
		cfgFile = out
	}

	fmt.Println()
	fmt.Println(sep)
	fmt.Printf("  %s\n", ac(aDim, "Нажмите любую клавишу для продолжения..."))
	for {
		k := <-keys
		if k != "↑" && k != "↓" {
			break
		}
	}
	return cfgFile, nil
}

// ── First-run guided wizard ───────────────────────────────

func firstRunSetup(cfgFile string, keys <-chan string) (string, bool) {
	cfg, _ := config.Load(cfgFile)
	s, _ := state.Load(cfg.StateFile)

	for {
		url, ok := wizardInputStep(keys,
			"НАСТРОЙКА АГЕНТА", "Шаг 1 из 3",
			"Адрес сервера Umbrella:", "Пример: api.umbrella.su:8443",
			false, cfg.ServerURL)
		if !ok {
			return cfgFile, false
		}
		url = strings.TrimSpace(url)
		if url == "" {
			url = cfg.ServerURL
		}
		if url == "" {
			continue
		}
		cfg.ServerURL = url

		token, ok := wizardInputStep(keys,
			"НАСТРОЙКА АГЕНТА", "Шаг 2 из 3",
			"Токен регистрации:", "Выдаётся в консоли Umbrella",
			true, "")
		if !ok {
			return cfgFile, false
		}
		token = strings.TrimSpace(token)
		if token == "" {
			continue
		}
		cfg.EnrollmentToken = token

		insecure, ok := wizardYesNoStep(keys,
			"НАСТРОЙКА АГЕНТА", "Шаг 3 из 3",
			"Пропустить проверку TLS-сертификата сервера?",
			"Только для тестовых окружений. В production выберите Нет.")
		if !ok {
			return cfgFile, false
		}
		cfg.InsecureSkipVerify = insecure

		newFile, err := enrollStep(keys, &cfg, s, cfgFile)
		if err != nil {
			for {
				k := <-keys
				switch k {
				case "r", "R":
					goto retryWizard
				case "q", "Q", kCtrlC:
					return cfgFile, false
				}
			}
		}
		return newFile, true

	retryWizard:
	}
}

// ── Verify screen ─────────────────────────────────────────

type checkResult struct {
	label  string
	status string
	detail string
}

func renderVerify(results []checkResult) {
	sep := wizardSep()
	fmt.Print("\033[2J\033[H")
	fmt.Printf("  %s\n", ac(aBold+aCyan, "ПРОВЕРКА СОЕДИНЕНИЯ"))
	fmt.Println(sep)
	fmt.Println()
	for _, r := range results {
		var icon string
		switch r.status {
		case "ok":
			icon = ac(aGreen, "✓")
		case "fail":
			icon = ac(aRed, "✗")
		case "skip":
			icon = ac(aDim, "─")
		default:
			icon = ac(aDim, "…")
		}
		detail := r.detail
		if visLen(detail) > 36 {
			detail = string([]rune(detail)[:36]) + "..."
		}
		fmt.Printf("  %s  %-28s %s\n", icon, r.label, ac(aDim, detail))
	}
	fmt.Println()
}

func pingServerCheck(serverURL string, insecure bool) checkResult {
	if serverURL == "" {
		return checkResult{"Сервер доступен", "fail", "Server URL не задан"}
	}
	u := serverURL
	if !strings.Contains(u, "://") {
		u = "https://" + u
	}
	u = strings.TrimRight(u, "/") + "/health"

	tr := http.DefaultTransport.(*http.Transport).Clone()
	if insecure {
		tr.TLSClientConfig = &tls.Config{InsecureSkipVerify: true} //nolint:gosec
	}
	cl := &http.Client{Timeout: 5 * time.Second, Transport: tr}

	start := time.Now()
	resp, err := cl.Get(u)
	ms := time.Since(start).Milliseconds()
	if err != nil {
		return checkResult{"Сервер доступен", "fail", err.Error()}
	}
	resp.Body.Close()
	if resp.StatusCode < 400 {
		return checkResult{"Сервер доступен", "ok", fmt.Sprintf("%s   %dms", serverURL, ms)}
	}
	return checkResult{"Сервер доступен", "fail", resp.Status}
}

func runVerifyChecks(cfg config.Config, s *state.State, onStep func([]checkResult)) []checkResult {
	var results []checkResult
	push := func(r checkResult) {
		results = append(results, r)
		if onStep != nil {
			onStep(results)
		}
	}
	update := func(r checkResult) {
		results[len(results)-1] = r
		if onStep != nil {
			onStep(results)
		}
	}

	push(checkResult{"Сервер доступен", "…", ""})
	r1 := pingServerCheck(cfg.ServerURL, cfg.InsecureSkipVerify)
	update(r1)

	authDetail := "Bearer token"
	if s.CertPEM != "" {
		authDetail = "mTLS (сертификат)"
	}
	push(checkResult{"Режим авторизации", "ok", authDetail})

	if r1.status != "ok" {
		push(checkResult{"Heartbeat", "skip", "не проверено"})
		push(checkResult{"Получение команд", "skip", "не проверено"})
		return results
	}

	apiCl := api.New(cfg.ServerURL, cfg.InsecureSkipVerify)
	apiCl.SetToken(s.AgentToken)
	if s.CertPEM != "" {
		if err := apiCl.SetClientCert([]byte(s.CertPEM), []byte(s.KeyPEM), []byte(s.CACertPEM)); err != nil {
			push(checkResult{"Heartbeat", "fail", err.Error()})
			push(checkResult{"Получение команд", "skip", "не проверено"})
			return results
		}
	}

	push(checkResult{"Heartbeat", "…", ""})
	if err := apiCl.Heartbeat(api.HeartbeatRequest{}); err != nil {
		update(checkResult{"Heartbeat", "fail", err.Error()})
		push(checkResult{"Получение команд", "skip", "не проверено"})
		return results
	}
	update(checkResult{"Heartbeat", "ok", "OK"})

	push(checkResult{"Получение команд", "…", ""})
	if _, err := apiCl.PollCommands(); err != nil {
		update(checkResult{"Получение команд", "fail", err.Error()})
	} else {
		update(checkResult{"Получение команд", "ok", "OK"})
	}
	return results
}

func verifyScreen(cfg config.Config, s *state.State, keys <-chan string) {
	sep := wizardSep()
outer:
	for {
		results := runVerifyChecks(cfg, s, renderVerify)

		hasFail := false
		for _, r := range results {
			if r.status == "fail" {
				hasFail = true
				break
			}
		}

		if !hasFail {
			fmt.Printf("  %s\n\n", ac(aGreen, "Все проверки успешны."))
			fmt.Printf("  %s\n", ac(aDim, "Нажмите любую клавишу для продолжения..."))
			<-keys
			return
		}

		fmt.Printf("  %s\n\n", ac(aYellow, "Некоторые проверки не прошли."))
		fmt.Println(sep)
		fmt.Printf("  %s\n", ac(aDim, "[ r ] Повторить   [ q ] Выйти   [ Enter ] Продолжить"))
		for {
			k := <-keys
			switch k {
			case "r", "R":
				continue outer
			case "q", "Q", kCtrlC:
				tuiRestore()
				os.Exit(0)
			case kEnter:
				return
			}
		}
	}
}

// ── Final install screen (first-run) ─────────────────────

func finalInstallScreen(cfgFile string, cfg config.Config, s *state.State, keys <-chan string) {
	sep := wizardSep()
	fmt.Print("\033[2J\033[H")
	fmt.Printf("  %s\n", ac(aBold+aCyan, "УСТАНОВКА СЛУЖБЫ"))
	fmt.Println(sep)
	fmt.Println()

	fmt.Printf("  %s\n", ac(aBold, "Итоговая конфигурация:"))
	fmt.Printf("    Сервер:  %s\n", cfg.ServerURL)
	if s.IsEnrolled() {
		id := s.AgentID
		if len(id) > 20 {
			id = id[:8] + "..."
		}
		fmt.Printf("    Агент:   %s\n", id)
		authMode := "Bearer token"
		if s.CertPEM != "" {
			authMode = "mTLS (сертификат)"
		}
		fmt.Printf("    Auth:    %s\n", authMode)
	}
	fmt.Println()

	svcSt, _ := serviceStatus()
	if svcSt == "active" || svcSt == "running" {
		fmt.Printf("  %s  Служба уже запущена (%s)\n", ac(aGreen, "✓"), svcSt)
		fmt.Println()
		fmt.Println(sep)
		fmt.Printf("  %s\n", ac(aDim, "Готово! Нажмите любую клавишу..."))
		<-keys
		return
	}

	fmt.Printf("  Установка службы...  ")
	if err := installService(cfgFile); err != nil {
		fmt.Printf("%s\n\n  %v\n\n", ac(aRed, "ОШИБКА"), err)
		fmt.Println(sep)
		fmt.Printf("  %s\n", ac(aDim, "Нажмите любую клавишу..."))
		<-keys
		return
	}
	fmt.Println(ac(aGreen, "OK"))

	fmt.Printf("  Запуск службы...     ")
	if err := startService(); err != nil {
		fmt.Printf("%s\n\n  %v\n", ac(aRed, "ОШИБКА"), err)
	} else {
		fmt.Println(ac(aGreen, "OK"))
		fmt.Printf("\n  %s\n", ac(aGreen, "✓ Агент запущен как системная служба."))
	}

	fmt.Println()
	fmt.Println(sep)
	fmt.Printf("  %s\n", ac(aDim, "Готово! Нажмите любую клавишу..."))
	<-keys
}

// ── Service install prompt (returning users) ──────────────

func serviceInstallPrompt(cfgFile string, keys <-chan string) {
	sep := wizardSep()
	fmt.Print("\033[2J\033[H")
	fmt.Printf("  %s\n\n", ac(aBold, "Служба не запущена. Установить?"))
	fmt.Printf("  %s\n", ac(aDim, "[ y ] Да   [ n ] Пропустить"))

	for {
		k := <-keys
		switch k {
		case "y", "Y":
			fmt.Print("\033[2J\033[H")
			fmt.Printf("  Установка службы...  ")
			if err := installService(cfgFile); err != nil {
				fmt.Printf("%s\n\n  %v\n", ac(aRed, "ОШИБКА"), err)
			} else {
				fmt.Println(ac(aGreen, "OK"))
				fmt.Printf("  Запуск службы...     ")
				if err := startService(); err != nil {
					fmt.Printf("%s\n\n  %v\n", ac(aRed, "ОШИБКА"), err)
				} else {
					fmt.Println(ac(aGreen, "OK"))
					fmt.Printf("\n  %s\n", ac(aGreen, "✓ Агент запущен."))
				}
			}
			fmt.Println()
			fmt.Println(sep)
			fmt.Printf("  %s\n", ac(aDim, "Нажмите любую клавишу..."))
			<-keys
			return
		case "n", "N", "q", "Q", kCtrlC, kEnter:
			return
		}
	}
}

// ── Monitor screen ────────────────────────────────────────

// tuiMonitor shows the live dashboard.
// Returns "logs", "policies", or "quit".
func tuiMonitor(cfgFile string, keys <-chan string) string {
	tick := time.NewTicker(autoRefresh)
	defer tick.Stop()

	redraw := func() {
		cfg, _ := config.Load(cfgFile)
		s, _ := state.Load(cfg.StateFile)
		svcSt, _ := serviceStatus()
		renderDashboard(cfg, s, svcSt, true, "[l] логи   [p] политики   [q] выход   auto-refresh: 3s")
	}
	redraw()

	for {
		select {
		case k := <-keys:
			switch k {
			case "l", "L":
				return "logs"
			case "p", "P":
				return "policies"
			case "q", "Q", kCtrlC:
				return "quit"
			case "r", "R":
				redraw()
				tick.Reset(autoRefresh)
			}
		case <-tick.C:
			redraw()
		}
	}
}

// ── Logs screen ───────────────────────────────────────────

// tuiLogs shows the log file tail.
// Returns true to go back to monitor, false to quit.
func tuiLogs(logFile string, keys <-chan string) bool {
	tick := time.NewTicker(2 * time.Second)
	defer tick.Stop()

	drawLogs(logFile)

	for {
		select {
		case k := <-keys:
			switch k {
			case "b", "B":
				return true
			case "q", "Q", kCtrlC:
				return false
			case "r", "R":
				drawLogs(logFile)
				tick.Reset(2 * time.Second)
			}
		case <-tick.C:
			drawLogs(logFile)
		}
	}
}

func drawLogs(logFile string) {
	sep := wizardSep()
	fmt.Print("\033[2J\033[H")
	fmt.Printf("  %s\n", ac(aBold+aCyan, "ЛОГИ АГЕНТА"))
	fmt.Println(sep)
	fmt.Println()

	if logFile == "" {
		fmt.Printf("  %s\n", ac(aDim, "лог-файл не настроен (log_file в конфиге)"))
	} else {
		lines := logTail(logFile, 50)
		if len(lines) == 0 {
			fmt.Printf("  %s\n", ac(aDim, "нет записей (служба ещё не запускалась)"))
		} else {
			for _, line := range lines {
				fmt.Printf("  %s\n", colorLogLine(line))
			}
		}
	}

	fmt.Println()
	fmt.Println(sep)
	fmt.Printf("  %s\n", ac(aDim, "[b] монитор   [r] обновить   auto-refresh: 2s"))
}

// logTail reads the last n lines from path.
func logTail(path string, n int) []string {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil
	}
	lines := strings.Split(strings.TrimRight(string(data), "\n"), "\n")
	if len(lines) > n {
		lines = lines[len(lines)-n:]
	}
	return lines
}

// ── Policies screen ───────────────────────────────────────

// tuiPolicies shows applied policies from the on-disk snapshot.
// Returns true to go back to monitor, false to quit.
func tuiPolicies(stateFile string, keys <-chan string) bool {
	tick := time.NewTicker(5 * time.Second)
	defer tick.Stop()

	drawPolicies(stateFile)

	for {
		select {
		case k := <-keys:
			switch k {
			case "b", "B":
				return true
			case "q", "Q", kCtrlC:
				return false
			case "r", "R":
				drawPolicies(stateFile)
				tick.Reset(5 * time.Second)
			}
		case <-tick.C:
			drawPolicies(stateFile)
		}
	}
}

func drawPolicies(stateFile string) {
	const w = 52
	sep := "  " + strings.Repeat("─", w)

	fmt.Print("\033[2J\033[H")

	title := "ПОЛИТИКИ АГЕНТА"
	ts := time.Now().Format("15:04:05")
	pad := w - len(title) - len(ts)
	if pad < 1 {
		pad = 1
	}
	fmt.Printf("  %s%s%s\n", ac(aBold+aCyan, title), strings.Repeat(" ", pad), ts)
	fmt.Println(sep)
	fmt.Println()

	ps, psErr := enforce.LoadState(stateFile)
	if psErr != nil {
		fmt.Printf("  %s\n", ac(aRed, "Ошибка чтения: "+psErr.Error()))
		fmt.Printf("  %s\n", ac(aDim, enforce.PolicyStatePath(stateFile)))
		fmt.Println()
		fmt.Println(sep)
		fmt.Printf("  %s\n", ac(aDim, "[b] монитор   [r] обновить   auto-refresh: 5s"))
		return
	}
	if ps == nil {
		fmt.Printf("  %s\n", ac(aYellow, "Нет данных — агент ещё не опросил сервер."))
		fmt.Printf("  %s\n", ac(aDim, "Ожидаемый файл: "+enforce.PolicyStatePath(stateFile)))
		fmt.Println()
		fmt.Println(sep)
		fmt.Printf("  %s\n", ac(aDim, "[b] монитор   [r] обновить   auto-refresh: 5s"))
		return
	}

	age := time.Since(ps.AppliedAt)
	ageStr := humanDur(age) + " назад"
	if age < 5*time.Second {
		ageStr = "только что"
	}
	fmt.Printf("  Обновлено: %s  (%s)   всего: %d\n",
		ac(aDim, ps.AppliedAt.Local().Format("15:04:05")),
		ac(aDim, ageStr),
		len(ps.Policies),
	)
	fmt.Println()

	if len(ps.Policies) == 0 {
		fmt.Printf("  %s\n", ac(aDim, "Политик нет."))
		fmt.Println()
		fmt.Println(sep)
		fmt.Printf("  %s\n", ac(aDim, "[b] монитор   [r] обновить   auto-refresh: 5s"))
		return
	}

	for _, p := range ps.Policies {
		// Header: action badge + kind + name
		var actionColor, actionBadge string
		if p.Action == "block" {
			actionColor = aRed
			actionBadge = "● BLOCK"
		} else {
			actionColor = aGreen
			actionBadge = "○ ALLOW"
		}
		name := p.Name
		if name == "" {
			name = p.ID
		}
		fmt.Printf("  %s  %s  %s\n",
			ac(actionColor, actionBadge),
			ac(aDim, p.Kind),
			ac(aBold, name),
		)

		// Rule type summary lines.
		if p.Domains > 0 {
			fmt.Printf("      %s  домены: %d\n", rulesIcon(p.Domains), p.Domains)
		}
		if p.IPs > 0 {
			fmt.Printf("      %s  IP-адреса: %d\n", rulesIcon(p.IPs), p.IPs)
		}
		if p.Processes > 0 {
			fmt.Printf("      %s  процессы: %d\n", rulesIcon(p.Processes), p.Processes)
		}
		if p.URLs > 0 {
			fmt.Printf("      %s  URL: %d %s\n", ac(aDim, "·"), p.URLs, ac(aDim, "(не применяется в phase 1)"))
		}
		if p.Domains == 0 && p.IPs == 0 && p.Processes == 0 && p.URLs == 0 {
			fmt.Printf("      %s\n", ac(aDim, "· нет правил"))
		}
		fmt.Println()
	}

	fmt.Println(sep)
	fmt.Printf("  %s\n", ac(aDim, "[b] монитор   [r] обновить   auto-refresh: 5s"))
}

func rulesIcon(count int) string {
	if count > 0 {
		return ac(aGreen, "✓")
	}
	return ac(aDim, "·")
}

// colorLogLine colours a slog text-format line by level keyword.
func colorLogLine(line string) string {
	up := strings.ToUpper(line)
	switch {
	case strings.Contains(up, "LEVEL=ERROR") || strings.Contains(up, " ERR "):
		return ac(aRed, line)
	case strings.Contains(up, "LEVEL=WARN"):
		return ac(aYellow, line)
	case strings.Contains(up, "LEVEL=DEBUG"):
		return ac(aDim, line)
	default:
		return line
	}
}
