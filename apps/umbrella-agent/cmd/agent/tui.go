package main

import (
	"crypto/tls"
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"runtime"
	"strings"
	"time"

	"golang.org/x/term"

	"github.com/flow-ecosystem/umbrella-agent/internal/agent"
	"github.com/flow-ecosystem/umbrella-agent/internal/api"
	"github.com/flow-ecosystem/umbrella-agent/internal/config"
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

// visLen returns the visible rune count, stripping ANSI escape sequences.
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
	kUp    = "↑"
	kDown  = "↓"
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
			if n >= 3 && b[0] == 0x1b && b[1] == '[' {
				switch b[2] {
				case 'A':
					ch <- kUp
				case 'B':
					ch <- kDown
				}
				continue
			}
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

// ── Screens ───────────────────────────────────────────────

type screen int

const (
	scrMenu screen = iota
	scrMonitor
	scrLogs
	scrDebug
	scrQuit
)

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
		// First run: guided wizard → verify → install service
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
		// Returning user: verify, then handle service state
		verifyScreen(cfg, s, keys)
		svcSt, _ := serviceStatus()
		if svcSt != "active" && svcSt != "running" {
			serviceInstallPrompt(cfgFile, keys)
		}
	}

	sel, cur := 0, scrMenu
	for cur != scrQuit {
		switch cur {
		case scrMenu:
			cur, sel = menuLoop(cfgFile, keys, sel)
		case scrMonitor:
			monitorScreen(cfgFile, keys)
			cur = scrMenu
		case scrLogs:
			logsScreen(keys)
			cur = scrMenu
		case scrDebug:
			debugScreen(cfgFile, keys)
			cur = scrMenu
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

// rawInput reads a line in raw mode. Cursor must already be positioned on
// the input row. Uses \r+\033[K to redraw in place. Returns ("", false) on Ctrl+C.
func rawInput(keys <-chan string, mask bool, initial string) (string, bool) {
	buf := []byte(initial)
	fmt.Print("\033[?25h") // show cursor

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

// wizardInputStep draws a full-screen input step and returns the entered value.
// The screen layout is fixed at 10 rows so cursor positioning is deterministic.
func wizardInputStep(keys <-chan string, title, step, label, hint string, mask bool, initial string) (string, bool) {
	sep := wizardSep()
	fmt.Print("\033[2J\033[H")
	// Row 1: title + step indicator
	fmt.Printf("  %-44s%s\n", ac(aBold+aCyan, title), ac(aDim, step))
	// Row 2: separator
	fmt.Println(sep)
	// Row 3: empty
	fmt.Println()
	// Row 4: label
	fmt.Printf("  %s\n", label)
	// Row 5: hint (always printed; empty line if no hint)
	if hint != "" {
		fmt.Printf("  %s\n", ac(aDim, hint))
	} else {
		fmt.Println()
	}
	// Row 6: empty
	fmt.Println()
	// Row 7: input line (empty placeholder — rawInput draws here)
	fmt.Println()
	// Row 8: empty
	fmt.Println()
	// Row 9: separator
	fmt.Println(sep)
	// Row 10: footer
	fmt.Printf("  %s\n", ac(aDim, "Enter — далее   Ctrl+C — отмена"))
	// Cursor is now at Row 11; move up 4 to reach Row 7 (input placeholder)
	fmt.Print("\033[4A")

	return rawInput(keys, mask, initial)
}

// wizardYesNoStep draws a full-screen y/n step. Returns (choice, ok).
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
		// wrap long error message
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
		if k != kUp && k != kDown {
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
		// Step 1: Server URL
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

		// Step 2: Enrollment token
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

		// Step 3: TLS
		insecure, ok := wizardYesNoStep(keys,
			"НАСТРОЙКА АГЕНТА", "Шаг 3 из 3",
			"Пропустить проверку TLS-сертификата сервера?",
			"Только для тестовых окружений. В production выберите Нет.")
		if !ok {
			return cfgFile, false
		}
		cfg.InsecureSkipVerify = insecure

		// Enroll
		newFile, err := enrollStep(keys, &cfg, s, cfgFile)
		if err != nil {
			// enrollStep printed the error and the [ r ] / [ q ] prompt
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
	status string // "ok", "fail", "skip", "…"
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

// ── Final install screen (first-run mandatory) ────────────

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
		fmt.Printf("  %s\n", ac(aDim, "Настройка завершена! Нажмите любую клавишу..."))
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
	fmt.Printf("  %s\n", ac(aDim, "Настройка завершена! Нажмите любую клавишу..."))
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

// ── Main menu ─────────────────────────────────────────────

type item struct {
	n     string
	label string
	off   bool
}

func menuLoop(cfgFile string, keys <-chan string, initSel int) (screen, int) {
	sel := initSel
	tick := time.NewTicker(3 * time.Second)
	defer tick.Stop()

	var items []item
	draw := func() {
		cfg, _ := config.Load(cfgFile)
		s, _ := state.Load(cfg.StateFile)
		svcSt, _ := serviceStatus()
		items = menuItems(s, svcSt)
		drawMenu(cfg, s, svcSt, items, sel)
	}
	draw()

	for {
		select {
		case k := <-keys:
			switch k {
			case kUp:
				for {
					if sel--; sel < 0 {
						sel = len(items) - 1
					}
					if !items[sel].off {
						break
					}
				}
				draw()
			case kDown:
				for {
					if sel++; sel >= len(items) {
						sel = 0
					}
					if !items[sel].off {
						break
					}
				}
				draw()
			case kEnter:
				if !items[sel].off {
					return execItem(cfgFile, items[sel].n, keys)
				}
			case "q", "Q", kCtrlC:
				return scrQuit, sel
			default:
				for i, it := range items {
					if k == it.n && !it.off {
						sel = i
						return execItem(cfgFile, it.n, keys)
					}
				}
			}
		case <-tick.C:
			draw()
		}
	}
}

func menuItems(s *state.State, svcSt string) []item {
	running := svcSt == "active" || svcSt == "running"
	enrolled := s.IsEnrolled()
	svcLabel := "Запустить службу"
	if running {
		svcLabel = "Остановить службу"
	}
	return []item{
		{"1", "Настроить агент", false},
		{"2", svcLabel, !enrolled},
		{"3", "Мониторинг", false},
		{"4", "Логи", false},
		{"5", "Отладка", false},
		{"6", "Удалить агент", false},
	}
}

func drawMenu(cfg config.Config, s *state.State, svcSt string, items []item, sel int) {
	const w = 52
	sep := "  " + strings.Repeat("─", w)

	fmt.Print("\033[2J\033[H")
	fmt.Printf("  %s\n", ac(aBold+aCyan, "UMBRELLA AGENT"))
	fmt.Printf("  %s\n", ac(aDim, "v"+cfg.AgentVersion))
	fmt.Println(sep)
	fmt.Println()

	running := svcSt == "active" || svcSt == "running"
	if running {
		fmt.Printf("  Служба:  %s\n", ac(aGreen, "● "+svcSt))
	} else {
		fmt.Printf("  Служба:  %s\n", ac(aRed, "○ "+svcSt))
	}
	if s.IsEnrolled() {
		short := s.AgentID
		if len(short) > 36 {
			short = short[:8] + "..." + short[len(short)-4:]
		}
		fmt.Printf("  Агент:   %s\n", short)
		if cfg.ServerURL != "" {
			fmt.Printf("  Сервер:  %s\n", cfg.ServerURL)
		} else {
			fmt.Printf("  Сервер:  %s\n", ac(aYellow, "не задан"))
		}
	} else {
		fmt.Printf("  Агент:   %s\n", ac(aYellow, "не зарегистрирован"))
	}
	fmt.Println()
	fmt.Println(sep)
	fmt.Println()

	for i, it := range items {
		switch {
		case it.off:
			fmt.Printf("     %s\n", ac(aDim, it.n+". "+it.label))
		case i == sel:
			fmt.Printf("  %s %s\n", ac(aCyan, "▶"), ac(aBold, it.n+". "+it.label))
		default:
			fmt.Printf("     %s. %s\n", it.n, it.label)
		}
	}

	fmt.Println()
	fmt.Println(sep)
	fmt.Printf("  %s\n", ac(aDim, "↑↓ навигация   Enter выбрать   q выход"))
}

func execItem(cfgFile, n string, keys <-chan string) (screen, int) {
	switch n {
	case "1":
		setupScreen(cfgFile, keys)
		return scrMenu, 0
	case "2":
		serviceToggle(keys)
		return scrMenu, 1
	case "3":
		return scrMonitor, 2
	case "4":
		return scrLogs, 3
	case "5":
		return scrDebug, 4
	case "6":
		uninstallScreen(keys)
		return scrMenu, 5
	}
	return scrMenu, 0
}

// ── Setup screen (menu item "1") ──────────────────────────

func setupScreen(cfgFile string, keys <-chan string) {
	term.Restore(tuiFD, tuiOldSt)
	fmt.Print("\033[?25h\033[2J\033[H")

	defer func() {
		fmt.Printf("\n  %s\n", ac(aDim, "Нажмите Enter для продолжения..."))
		buf := make([]byte, 1)
		for {
			os.Stdin.Read(buf) //nolint:errcheck
			if buf[0] == 0x0d || buf[0] == 0x0a {
				break
			}
		}
		tuiRaw()
	}()

	cfg, err := config.Load(cfgFile)
	if err != nil {
		fmt.Printf("  Ошибка загрузки конфига: %v\n", err)
		return
	}
	s, err := state.Load(cfg.StateFile)
	if err != nil {
		fmt.Printf("  Ошибка загрузки состояния: %v\n", err)
		return
	}

	if !s.IsEnrolled() {
		cfgFile = runWizard(&cfg, s, cfgFile)
		if cfgFile == "" {
			return
		}
	} else {
		fmt.Printf("  Агент уже зарегистрирован: %s\n\n", s.AgentID)
	}

	fmt.Print("  Установка службы... ")
	if err := installService(cfgFile); err != nil {
		fmt.Printf("ОШИБКА\n  %v\n", err)
		return
	}
	fmt.Println("OK")

	fmt.Print("  Запуск службы...    ")
	if err := startService(); err != nil {
		fmt.Printf("ОШИБКА\n  %v\n", err)
		return
	}
	fmt.Println("OK")
	fmt.Printf("\n  %s\n", ac(aGreen, "✓ Агент установлен и запущен как системная служба."))
}

// ── Service toggle ────────────────────────────────────────

func serviceToggle(keys <-chan string) {
	fmt.Print("\033[2J\033[H")
	svcSt, _ := serviceStatus()
	running := svcSt == "active" || svcSt == "running"

	if running {
		fmt.Printf("  %s\n\n", ac(aBold, "Остановка службы..."))
		if err := stopService(); err != nil {
			fmt.Printf("  %s\n", ac(aRed, "Ошибка: "+err.Error()))
		} else {
			fmt.Printf("  %s\n", ac(aGreen, "✓ Служба остановлена"))
		}
	} else {
		fmt.Printf("  %s\n\n", ac(aBold, "Запуск службы..."))
		if err := startService(); err != nil {
			fmt.Printf("  %s\n", ac(aRed, "Ошибка: "+err.Error()))
		} else {
			fmt.Printf("  %s\n", ac(aGreen, "✓ Служба запущена"))
		}
	}

	fmt.Printf("\n  %s\n", ac(aDim, "Нажмите любую клавишу..."))
	<-keys
}

// ── Uninstall screen ──────────────────────────────────────

func uninstallScreen(keys <-chan string) {
	fmt.Print("\033[2J\033[H")
	fmt.Printf("  %s\n\n", ac(aBold+aRed, "Удалить агент?"))
	fmt.Println("  Служба будет остановлена и удалена из системы.")
	fmt.Println("  Файлы конфига и state останутся на диске.")
	fmt.Printf("\n  %s\n", ac(aDim, "[y] Да   [любая другая] Отмена"))

	k := <-keys
	if k != "y" && k != "Y" {
		return
	}

	fmt.Print("\033[2J\033[H")
	fmt.Print("  Остановка службы...     ")
	_ = stopService()
	fmt.Println("OK")

	fmt.Print("  Удаление службы...      ")
	if err := uninstallService(); err != nil {
		fmt.Printf("ОШИБКА\n  %v\n", ac(aRed, err.Error()))
	} else {
		fmt.Println("OK")
		fmt.Printf("\n  %s\n", ac(aGreen, "✓ Агент удалён"))
	}
	fmt.Printf("\n  %s\n", ac(aDim, "Нажмите любую клавишу..."))
	<-keys
}

// ── Logs screen ───────────────────────────────────────────

func logsScreen(keys <-chan string) {
	if runtime.GOOS == "windows" {
		sep := wizardSep()
		fmt.Print("\033[2J\033[H")
		fmt.Printf("  %s\n", ac(aBold+aCyan, "ЛОГИ АГЕНТА"))
		fmt.Println(sep)
		fmt.Println()
		fmt.Println("  Для просмотра логов откройте Event Viewer:")
		fmt.Println()
		fmt.Printf("    %s\n", ac(aBold, "eventvwr.msc"))
		fmt.Println("    → Windows Logs → Application")
		fmt.Printf("    → Источник: %s\n", ac(aCyan, "UmbrellaAgent"))
		fmt.Println()
		fmt.Println(sep)
		fmt.Printf("  %s\n", ac(aDim, "[b] назад"))
		for {
			k := <-keys
			if k == "b" || k == "B" || k == "q" || k == "Q" || k == kCtrlC {
				return
			}
		}
	}

	tick := time.NewTicker(2 * time.Second)
	defer tick.Stop()
	drawLogs()

	for {
		select {
		case k := <-keys:
			switch k {
			case "b", "B", "q", "Q", kCtrlC:
				return
			case "r", "R":
				drawLogs()
				tick.Reset(2 * time.Second)
			}
		case <-tick.C:
			drawLogs()
		}
	}
}

func drawLogs() {
	sep := wizardSep()
	fmt.Print("\033[2J\033[H")
	fmt.Printf("  %s\n", ac(aBold+aCyan, "ЛОГИ АГЕНТА"))
	fmt.Println(sep)
	fmt.Println()

	out, err := exec.Command(
		"journalctl", "-u", "umbrella-agent",
		"-n", "40", "--no-pager", "--output=short-iso", "--quiet",
	).Output()
	if err != nil || len(out) == 0 {
		fmt.Printf("  %s\n", ac(aDim, "нет записей (служба не запускалась или journalctl недоступен)"))
	} else {
		for _, line := range strings.Split(strings.TrimRight(string(out), "\n"), "\n") {
			fmt.Printf("  %s\n", colorLogLine(line))
		}
	}

	fmt.Println()
	fmt.Println(sep)
	fmt.Printf("  %s\n", ac(aDim, "[b] назад   [r] обновить   auto-refresh: 2s"))
}

func colorLogLine(line string) string {
	up := strings.ToUpper(line)
	switch {
	case strings.Contains(up, "ERROR") || strings.Contains(up, " ERR "):
		return ac(aRed, line)
	case strings.Contains(up, "WARN"):
		return ac(aYellow, line)
	default:
		return line
	}
}

// ── Monitor screen ────────────────────────────────────────

func monitorScreen(cfgFile string, keys <-chan string) {
	tick := time.NewTicker(autoRefresh)
	defer tick.Stop()

	redraw := func() {
		cfg, _ := config.Load(cfgFile)
		s, _ := state.Load(cfg.StateFile)
		svcSt, _ := serviceStatus()
		renderDashboard(cfg, s, svcSt, true, "[b] назад   [r] обновить   auto-refresh: 3s")
	}
	redraw()

	for {
		select {
		case k := <-keys:
			switch k {
			case "b", "B", "q", "Q", kCtrlC:
				return
			case "r", "R":
				redraw()
				tick.Reset(autoRefresh)
			}
		case <-tick.C:
			redraw()
		}
	}
}

// ── Debug screen ──────────────────────────────────────────

func debugScreen(cfgFile string, keys <-chan string) {
	connResult := ""
	draw := func() { drawDebug(cfgFile, connResult) }
	draw()

	for {
		k := <-keys
		switch k {
		case "b", "B", "q", "Q", kCtrlC:
			return
		case "t", "T":
			connResult = ac(aDim, "Проверяю...")
			draw()
			cfg, _ := config.Load(cfgFile)
			connResult = pingServer(cfg.ServerURL)
			draw()
		case "r", "R":
			draw()
		}
	}
}

func drawDebug(cfgFile string, connResult string) {
	cfg, _ := config.Load(cfgFile)
	s, _ := state.Load(cfg.StateFile)
	now := time.Now()

	const w = 52
	sep := "  " + strings.Repeat("─", w)

	fmt.Print("\033[2J\033[H")
	fmt.Printf("  %s\n", ac(aBold+aCyan, "ОТЛАДКА"))
	fmt.Println(sep)
	fmt.Println()

	fmt.Printf("  %s\n", ac(aBold, "Файлы конфигурации"))
	fileRow("  config.json", config.DefaultConfigFile())
	fileRow("  state.json ", cfg.StateFile)
	fmt.Println()

	fmt.Printf("  %s\n", ac(aBold, "Конфигурация"))
	if cfg.ServerURL != "" {
		fmt.Printf("    Server URL:  %s\n", cfg.ServerURL)
	} else {
		fmt.Printf("    Server URL:  %s\n", ac(aYellow, "не задан"))
	}
	cmdSec := cfg.CommandPollIntervalSec
	if s.CommandPollIntervalSec > 0 {
		cmdSec = s.CommandPollIntervalSec
	}
	polSec := cfg.PolicyPollIntervalSec
	if s.PolicyPollIntervalSec > 0 {
		polSec = s.PolicyPollIntervalSec
	}
	fmt.Printf("    Команды:     каждые %ds\n", cmdSec)
	fmt.Printf("    Политики:    каждые %ds\n", polSec)
	fmt.Printf("    Heartbeat:   каждые %ds\n", cfg.HeartbeatIntervalSec)
	if cfg.InsecureSkipVerify {
		fmt.Printf("    TLS:         %s\n", ac(aYellow, "InsecureSkipVerify = true"))
	}
	fmt.Println()

	fmt.Printf("  %s\n", ac(aBold, "Состояние агента"))
	if s.IsEnrolled() {
		fmt.Printf("    ID:          %s\n", s.AgentID)
		fmt.Printf("    Enrolled:    %s\n", s.EnrolledAt.Format("2006-01-02 15:04:05"))
		certLeft := time.Until(s.CertExpiresAt)
		certStr := fmt.Sprintf("до %s  (%s)", s.CertExpiresAt.Format("2006-01-02"), humanDays(certLeft))
		if certLeft < 7*24*time.Hour {
			certStr = ac(aRed, certStr)
		} else {
			certStr = ac(aGreen, certStr)
		}
		fmt.Printf("    Сертификат:  %s\n", certStr)
		if s.LastHeartbeatAt != nil {
			age := now.Sub(*s.LastHeartbeatAt)
			beat := fmt.Sprintf("%s  (%s назад)", s.LastHeartbeatAt.Format("15:04:05"), humanDur(age))
			if age > 2*time.Minute {
				beat = ac(aRed, beat)
			} else {
				beat = ac(aGreen, beat)
			}
			fmt.Printf("    Last beat:   %s\n", beat)
		} else {
			fmt.Printf("    Last beat:   %s\n", ac(aYellow, "нет данных (агент не запускался)"))
		}
	} else {
		fmt.Printf("    %s\n", ac(aYellow, "не зарегистрирован"))
	}
	fmt.Println()

	fmt.Printf("  %s\n", ac(aBold, "Соединение с сервером"))
	if connResult != "" {
		fmt.Printf("    %s\n", connResult)
	} else {
		fmt.Printf("    %s\n", ac(aDim, "[t] нажмите для проверки"))
	}
	fmt.Println()

	fmt.Printf("  %s\n", ac(aBold, "Последние события"))
	if logs := recentLogs(); logs != "" {
		for _, line := range strings.Split(strings.TrimRight(logs, "\n"), "\n") {
			fmt.Printf("    %s\n", ac(aDim, line))
		}
	} else {
		note := "недоступно"
		if runtime.GOOS == "windows" {
			note = "откройте Event Viewer → Windows Logs → Application"
		}
		fmt.Printf("    %s\n", ac(aDim, note))
	}
	fmt.Println()

	fmt.Println(sep)
	fmt.Printf("  %s\n", ac(aDim, "[b] назад   [t] тест соединения   [r] обновить"))
}

func fileRow(label, path string) {
	if _, err := os.Stat(path); err == nil {
		fmt.Printf("%s: %s\n", label, ac(aGreen, path))
	} else {
		fmt.Printf("%s: %s\n", label, ac(aRed, path+"  (не найден)"))
	}
}

func pingServer(serverURL string) string {
	if serverURL == "" {
		return ac(aRed, "Server URL не задан")
	}
	u := serverURL
	if !strings.Contains(u, "://") {
		u = "https://" + u
	}
	u = strings.TrimRight(u, "/") + "/health"

	start := time.Now()
	resp, err := (&http.Client{Timeout: 5 * time.Second}).Get(u)
	ms := time.Since(start).Milliseconds()
	if err != nil {
		return ac(aRed, fmt.Sprintf("недоступен: %v", err))
	}
	resp.Body.Close()
	if resp.StatusCode < 400 {
		return ac(aGreen, fmt.Sprintf("%s  %dms", resp.Status, ms))
	}
	return ac(aYellow, fmt.Sprintf("%s  %dms", resp.Status, ms))
}

func recentLogs() string {
	if runtime.GOOS != "linux" {
		return ""
	}
	out, err := exec.Command(
		"journalctl", "-u", "umbrella-agent",
		"-n", "10", "--no-pager", "--output=short-iso", "--quiet",
	).Output()
	if err != nil {
		return ""
	}
	return strings.TrimSpace(string(out))
}
