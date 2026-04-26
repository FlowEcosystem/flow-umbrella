//go:build windows

package enforce

import (
	"encoding/binary"
	"encoding/json"
	"fmt"
	"net"
	"os"
	"path/filepath"
	"unsafe"

	"golang.org/x/sys/windows"
)

// ── Constants ─────────────────────────────────────────────────────────────────

const (
	fwpUint8  uint32 = 1 // FWP_UINT8
	fwpUint16 uint32 = 2 // FWP_UINT16
	fwpUint32 uint32 = 3 // FWP_UINT32

	fwpMatchEqual uint32 = 0 // FWP_MATCH_EQUAL

	// FWP_ACTION_BLOCK already includes FWP_ACTION_FLAG_TERMINATING.
	fwpActionBlock uint32 = 0x00001001

	// FWPM_FILTER_FLAG_PERSISTENT — filter survives WFP engine restart and reboot.
	fwpmFilterFlagPersistent uint32 = 0x00000001

	rpcCAuthnWinnt uint32 = 0x0A

	wfpEAlreadyExists uint32 = 0x80320009 // FWP_E_ALREADY_EXISTS

	ipProtoTCP uint8 = 6
	ipProtoUDP uint8 = 17
)

// ── GUIDs ─────────────────────────────────────────────────────────────────────

var (
	// FWPM_LAYER_ALE_AUTH_CONNECT_V4 — outbound IPv4 connection layer.
	guidLayerAleAuthConnectV4 = windows.GUID{
		Data1: 0xc38d57d1, Data2: 0x05a7, Data3: 0x4c33,
		Data4: [8]byte{0x90, 0x4f, 0x7f, 0xbc, 0xee, 0xe6, 0x0e, 0x82},
	}
	// FWPM_CONDITION_IP_REMOTE_ADDRESS
	guidConditionRemoteAddr = windows.GUID{
		Data1: 0xb235ae9a, Data2: 0x1d64, Data3: 0x49b8,
		Data4: [8]byte{0xa4, 0x4c, 0x5f, 0xf3, 0xd9, 0x09, 0x50, 0x45},
	}
	// FWPM_CONDITION_IP_REMOTE_PORT
	guidConditionRemotePort = windows.GUID{
		Data1: 0xc35a604d, Data2: 0xd22b, Data3: 0x4e1a,
		Data4: [8]byte{0x91, 0xb4, 0x68, 0xf6, 0x74, 0xee, 0x67, 0x4b},
	}
	// FWPM_CONDITION_IP_PROTOCOL
	guidConditionIPProto = windows.GUID{
		Data1: 0x3971ef2b, Data2: 0x623e, Data3: 0x4f9a,
		Data4: [8]byte{0x8c, 0xb1, 0x6e, 0x79, 0xb8, 0x06, 0xb9, 0xa7},
	}
	// Umbrella-specific sublayer GUID (arbitrary, stable).
	guidUmbrellaSublayer = windows.GUID{
		Data1: 0x4e6a1b7f, Data2: 0x3c2d, Data3: 0x4a8e,
		Data4: [8]byte{0x9b, 0x5f, 0x1a, 0x2c, 0x3d, 0x4e, 0x5f, 0x60},
	}
)

// ── C-struct mirrors (sizes verified for Windows x64 / AMD64) ─────────────────

// fwpByteBlob mirrors FWP_BYTE_BLOB (16 bytes).
type fwpByteBlob struct {
	size uint32
	_    uint32  // align data pointer to 8 bytes
	data uintptr
}

// fwpmDisplayData0 mirrors FWPM_DISPLAY_DATA0 (16 bytes).
type fwpmDisplayData0 struct {
	name        *uint16
	description *uint16
}

// fwpValue0 mirrors FWP_VALUE0 / FWP_CONDITION_VALUE0 (16 bytes).
// val holds uint8/uint16/uint32 values in the low bytes on little-endian.
type fwpValue0 struct {
	typ uint32
	_   uint32
	val uint64
}

// fwpmFilterCondition0 mirrors FWPM_FILTER_CONDITION0 (40 bytes).
type fwpmFilterCondition0 struct {
	fieldKey  windows.GUID
	matchType uint32
	_         uint32 // pad condValue to 8-byte boundary
	condValue fwpValue0
}

// fwpmAction0 mirrors FWPM_ACTION0 (20 bytes).
type fwpmAction0 struct {
	typ  uint32
	guid [16]byte
}

// fwpmFilter0 mirrors FWPM_FILTER0 (208 bytes).
//
// Offsets (x64):
//
//	  0 filterKey       16  displayData     32 flags
//	 36 _pad0           40 providerKey      48 providerData
//	 64 layerKey        80 subLayerKey      96 weight
//	112 numFilterConditions  116 _pad1      120 filterConditions
//	128 action(20)     148 _pad2           152 _unionPad(16)
//	168 reserved       184 filterId        192 effectiveWeight
type fwpmFilter0 struct {
	filterKey           windows.GUID     // 0
	displayData         fwpmDisplayData0 // 16
	flags               uint32           // 32
	_pad0               uint32           // 36
	providerKey         uintptr          // 40
	providerData        fwpByteBlob      // 48
	layerKey            windows.GUID     // 64
	subLayerKey         windows.GUID     // 80
	weight              fwpValue0        // 96
	numFilterConditions uint32           // 112
	_pad1               uint32           // 116
	filterConditions    uintptr          // 120
	action              fwpmAction0      // 128
	_pad2               uint32           // 148
	_unionPad           [16]byte         // 152 (rawContext / providerContextKey)
	reserved            windows.GUID     // 168
	filterId            uint64           // 184
	effectiveWeight     fwpValue0        // 192
}

// fwpmSublayer0 mirrors FWPM_SUBLAYER0 (72 bytes).
type fwpmSublayer0 struct {
	subLayerKey  windows.GUID     // 0
	displayData  fwpmDisplayData0 // 16
	flags        uint16           // 32
	_pad0        [6]byte          // 34 — align providerKey to 8 bytes
	providerKey  uintptr          // 40
	providerData fwpByteBlob      // 48
	weight       uint16           // 64
	_pad1        [6]byte          // 66 — round to 72 (struct align=8)
}

// ── DLL lazy load ─────────────────────────────────────────────────────────────

var (
	modFwpuclnt                = windows.NewLazySystemDLL("fwpuclnt.dll")
	procFwpmEngineOpen0        = modFwpuclnt.NewProc("FwpmEngineOpen0")
	procFwpmEngineClose0       = modFwpuclnt.NewProc("FwpmEngineClose0")
	procFwpmTransactionBegin0  = modFwpuclnt.NewProc("FwpmTransactionBegin0")
	procFwpmTransactionCommit0 = modFwpuclnt.NewProc("FwpmTransactionCommit0")
	procFwpmTransactionAbort0  = modFwpuclnt.NewProc("FwpmTransactionAbort0")
	procFwpmSubLayerAdd0       = modFwpuclnt.NewProc("FwpmSubLayerAdd0")
	procFwpmFilterAdd0         = modFwpuclnt.NewProc("FwpmFilterAdd0")
	procFwpmFilterDeleteById0  = modFwpuclnt.NewProc("FwpmFilterDeleteById0")
)

// ── Filter spec ───────────────────────────────────────────────────────────────

// filterSpec identifies one WFP filter: block outbound to ip[:port] via proto.
// port==0 means any port; proto==0 means any protocol (only valid when port==0).
type filterSpec struct {
	ip    string
	port  uint16
	proto uint8
}

func (s filterSpec) key() string {
	return fmt.Sprintf("%s,%d,%d", s.ip, s.port, s.proto)
}

// ── Filter ID persistence ─────────────────────────────────────────────────────

type wfpFilterRecord struct {
	Key      string `json:"key"`
	FilterID uint64 `json:"filter_id"`
}

func wfpStatePath(stateFile string) string {
	return filepath.Join(filepath.Dir(stateFile), "wfp-filters.json")
}

func wfpLoadState(stateFile string) map[string]uint64 {
	data, err := os.ReadFile(wfpStatePath(stateFile))
	if err != nil {
		return map[string]uint64{}
	}
	var records []wfpFilterRecord
	if err := json.Unmarshal(data, &records); err != nil {
		return map[string]uint64{}
	}
	m := make(map[string]uint64, len(records))
	for _, r := range records {
		m[r.Key] = r.FilterID
	}
	return m
}

func wfpSaveState(stateFile string, m map[string]uint64) error {
	records := make([]wfpFilterRecord, 0, len(m))
	for k, id := range m {
		records = append(records, wfpFilterRecord{Key: k, FilterID: id})
	}
	data, err := json.MarshalIndent(records, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(wfpStatePath(stateFile), data, 0o644)
}

// ── Engine helpers ────────────────────────────────────────────────────────────

func wfpOpenEngine() (uintptr, error) {
	var h uintptr
	r, _, _ := procFwpmEngineOpen0.Call(
		0, uintptr(rpcCAuthnWinnt), 0, 0,
		uintptr(unsafe.Pointer(&h)),
	)
	if r != 0 {
		return 0, fmt.Errorf("FwpmEngineOpen0: 0x%08X", r)
	}
	return h, nil
}

func wfpCloseEngine(h uintptr) { procFwpmEngineClose0.Call(h) }

func wfpBeginTx(h uintptr) error {
	r, _, _ := procFwpmTransactionBegin0.Call(h, 0)
	if r != 0 {
		return fmt.Errorf("FwpmTransactionBegin0: 0x%08X", r)
	}
	return nil
}

func wfpCommitTx(h uintptr) error {
	r, _, _ := procFwpmTransactionCommit0.Call(h)
	if r != 0 {
		return fmt.Errorf("FwpmTransactionCommit0: 0x%08X", r)
	}
	return nil
}

func wfpAbortTx(h uintptr) { procFwpmTransactionAbort0.Call(h) }

func wfpEnsureSublayer(h uintptr) error {
	name, _ := windows.UTF16PtrFromString("Umbrella Policy Sublayer")
	sl := fwpmSublayer0{
		subLayerKey: guidUmbrellaSublayer,
		displayData: fwpmDisplayData0{name: name},
		weight:      0x0100,
	}
	r, _, _ := procFwpmSubLayerAdd0.Call(h, uintptr(unsafe.Pointer(&sl)), 0)
	if r != 0 && uint32(r) != wfpEAlreadyExists {
		return fmt.Errorf("FwpmSubLayerAdd0: 0x%08X", r)
	}
	return nil
}

// wfpAddFilter creates one block filter and returns its WFP-assigned ID.
func wfpAddFilter(h uintptr, spec filterSpec) (uint64, error) {
	ip4 := net.ParseIP(spec.ip).To4()
	if ip4 == nil {
		return 0, fmt.Errorf("invalid IPv4: %s", spec.ip)
	}
	// WFP expects IPv4 addresses in host byte order (big-endian uint32 = network order).
	ipVal := binary.BigEndian.Uint32(ip4)

	var conds [3]fwpmFilterCondition0
	n := 0

	conds[n] = fwpmFilterCondition0{
		fieldKey:  guidConditionRemoteAddr,
		matchType: fwpMatchEqual,
		condValue: fwpValue0{typ: fwpUint32, val: uint64(ipVal)},
	}
	n++

	if spec.proto != 0 {
		conds[n] = fwpmFilterCondition0{
			fieldKey:  guidConditionIPProto,
			matchType: fwpMatchEqual,
			condValue: fwpValue0{typ: fwpUint8, val: uint64(spec.proto)},
		}
		n++
	}

	if spec.port != 0 {
		conds[n] = fwpmFilterCondition0{
			fieldKey:  guidConditionRemotePort,
			matchType: fwpMatchEqual,
			condValue: fwpValue0{typ: fwpUint16, val: uint64(spec.port)},
		}
		n++
	}

	displayName, _ := windows.UTF16PtrFromString("Umbrella-" + spec.key())

	var filterID uint64
	f := fwpmFilter0{
		flags:               fwpmFilterFlagPersistent,
		displayData:         fwpmDisplayData0{name: displayName},
		layerKey:            guidLayerAleAuthConnectV4,
		subLayerKey:         guidUmbrellaSublayer,
		weight:              fwpValue0{typ: fwpUint8, val: 15},
		numFilterConditions: uint32(n),
		filterConditions:    uintptr(unsafe.Pointer(&conds[0])),
		action:              fwpmAction0{typ: fwpActionBlock},
	}

	r, _, _ := procFwpmFilterAdd0.Call(
		h,
		uintptr(unsafe.Pointer(&f)),
		0,
		uintptr(unsafe.Pointer(&filterID)),
	)
	if r != 0 {
		return 0, fmt.Errorf("FwpmFilterAdd0(%s): 0x%08X", spec.key(), r)
	}
	return filterID, nil
}

func wfpDeleteFilter(h uintptr, id uint64) {
	procFwpmFilterDeleteById0.Call(h, uintptr(id))
}

