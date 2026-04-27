//go:build windows

package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"time"

	"golang.org/x/sys/windows/svc"
	"golang.org/x/sys/windows/svc/mgr"
)

const (
	serviceName        = "UmbrellaAgent"
	serviceDisplayName = "Umbrella Agent"
	serviceDesc        = "Umbrella security endpoint management agent"
)

// isServiceMode reports whether this process was started by the Windows SCM.
func isServiceMode() bool {
	ok, _ := svc.IsWindowsService()
	return ok
}

// runAsService hands control to the Windows SCM and blocks until the service
// is stopped. run is called in a goroutine and receives a done channel.
func runAsService(run func(<-chan struct{})) error {
	return svc.Run(serviceName, &handler{run: run})
}

type handler struct {
	run func(<-chan struct{})
}

func (h *handler) Execute(_ []string, r <-chan svc.ChangeRequest, s chan<- svc.Status) (bool, uint32) {
	const accepts = svc.AcceptStop | svc.AcceptShutdown
	running := svc.Status{State: svc.Running, Accepts: accepts}

	s <- running

	done := make(chan struct{})
	go h.run(done)

	for c := range r {
		switch c.Cmd {
		case svc.Interrogate:
			s <- c.CurrentStatus
		case svc.Stop, svc.Shutdown:
			s <- svc.Status{State: svc.StopPending}
			close(done)
			return false, 0
		default:
			s <- running
		}
	}
	return false, 0
}

// installService registers the binary with the Windows SCM as an
// auto-start service running as LocalSystem (SYSTEM).
// cfgFile is currently unused on Windows — the service auto-discovers
// config.json from the exe directory at runtime.
func installService(_ string) error {
	exePath, err := os.Executable()
	if err != nil {
		return fmt.Errorf("get exe path: %w", err)
	}
	exePath, err = filepath.Abs(exePath)
	if err != nil {
		return fmt.Errorf("abs path: %w", err)
	}

	m, err := mgr.Connect()
	if err != nil {
		return fmt.Errorf("connect to SCM (run as Administrator): %w", err)
	}
	defer m.Disconnect()

	// Return a friendly error if it already exists.
	if s, err := m.OpenService(serviceName); err == nil {
		s.Close()
		return fmt.Errorf("service %q already exists (run 'uninstall' first)", serviceName)
	}

	s, err := m.CreateService(serviceName, exePath, mgr.Config{
		DisplayName:      serviceDisplayName,
		Description:      serviceDesc,
		StartType:        mgr.StartAutomatic,
		ServiceStartName: "", // empty string → LocalSystem (SYSTEM)
	})
	if err != nil {
		return fmt.Errorf("create service: %w", err)
	}
	defer s.Close()

	// Restart immediately on any crash, up to 3 times; reset counter after 24h.
	recovery := []mgr.RecoveryAction{
		{Type: mgr.ServiceRestart, Delay: 0},
		{Type: mgr.ServiceRestart, Delay: 0},
		{Type: mgr.ServiceRestart, Delay: 0},
	}
	if err := s.SetRecoveryActions(recovery, 86400); err != nil {
		fmt.Printf("warning: could not set recovery actions: %v\n", err)
	}

	// Restrict the service DACL: only SYSTEM has full control.
	// Admins and Users can query status but cannot stop, delete, or reconfigure.
	const sddl = `D:(A;;CCLCSWRPWPDTLOCRSDRCWDWO;;;SY)(A;;CCLCRC;;;BA)(A;;CCLCRC;;;BU)`
	if err := exec.Command("sc", "sdset", serviceName, sddl).Run(); err != nil {
		fmt.Printf("warning: could not set service DACL: %v\n", err)
	}

	// Lock the installation directory: SYSTEM full control, everyone else read+execute.
	protectInstallDir(exePath)
	return nil
}

// protectInstallDir sets an ACL on the agent directory so only SYSTEM can
// write or delete files. Uses locale-independent SID syntax.
func protectInstallDir(exePath string) {
	dir := filepath.Dir(exePath)
	err := exec.Command("icacls", dir,
		"/inheritance:r",
		"/grant:r", "*S-1-5-18:(OI)(CI)(F)",   // SYSTEM: full control
		"/grant:r", "*S-1-5-32-544:(OI)(CI)(RX)", // Administrators: read+execute
		"/grant:r", "*S-1-5-32-545:(OI)(CI)(RX)", // Users: read+execute
		"/T",
	).Run()
	if err != nil {
		fmt.Printf("warning: could not set directory ACL: %v\n", err)
	}
}

func uninstallService() error {
	m, err := mgr.Connect()
	if err != nil {
		return fmt.Errorf("connect to SCM: %w", err)
	}
	defer m.Disconnect()

	s, err := m.OpenService(serviceName)
	if err != nil {
		return fmt.Errorf("service not found: %w", err)
	}
	defer s.Close()

	// Best-effort stop before deletion.
	if st, err := s.Query(); err == nil && st.State == svc.Running {
		_, _ = s.Control(svc.Stop)
		for range 20 {
			time.Sleep(250 * time.Millisecond)
			if st, err := s.Query(); err != nil || st.State == svc.Stopped {
				break
			}
		}
	}

	return s.Delete()
}

func startService() error {
	m, err := mgr.Connect()
	if err != nil {
		return fmt.Errorf("connect to SCM: %w", err)
	}
	defer m.Disconnect()

	s, err := m.OpenService(serviceName)
	if err != nil {
		return fmt.Errorf("open service: %w", err)
	}
	defer s.Close()

	return s.Start()
}

func stopService() error {
	m, err := mgr.Connect()
	if err != nil {
		return fmt.Errorf("connect to SCM: %w", err)
	}
	defer m.Disconnect()

	s, err := m.OpenService(serviceName)
	if err != nil {
		return fmt.Errorf("open service: %w", err)
	}
	defer s.Close()

	_, err = s.Control(svc.Stop)
	return err
}

func serviceStatus() (string, error) {
	m, err := mgr.Connect()
	if err != nil {
		// SCM требует прав администратора — возвращаем читаемое сообщение
		// вместо падения с "access denied".
		return "unknown (run as administrator to query SCM)", nil
	}
	defer m.Disconnect()

	s, err := m.OpenService(serviceName)
	if err != nil {
		return "not installed", nil
	}
	defer s.Close()

	st, err := s.Query()
	if err != nil {
		return "", err
	}

	switch st.State {
	case svc.Running:
		return "running", nil
	case svc.Stopped:
		return "stopped", nil
	case svc.StartPending:
		return "starting", nil
	case svc.StopPending:
		return "stopping", nil
	default:
		return fmt.Sprintf("state(%d)", st.State), nil
	}
}
