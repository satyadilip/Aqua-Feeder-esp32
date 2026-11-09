---
name: Requirement Verification (RTM)
about: Standard verification issue for an aquaCON system requirement
title: '[REQ-XXX] <Requirement Title>'
labels: ['requirement', 'status:pending']
assignees: ''
---

### 📋 Requirement Specification
- **ID**: `REQ-XXX`
- **Category**: `<Category Name>`
- **Verification Method**: `[T] Test` | `[I] Inspect` | `[A] Analysis` | `[D] Demo`
- **Target Hardware**: Feeder 03 (ESP32-S3)
- **Source Reference**: `<Source File>`

### 📝 Requirement Statement
> <Formal ISO 29148 Requirement Statement>

---

### 🧪 Verification & Acceptance Criteria
- [ ] **Pre-Conditions**: System configured and powered on.
- [ ] **Success Case 1**: <Expected behavior under normal operation>
- [ ] **Success Case 2**: <Expected timing / electrical measurement / LCD output>
- [ ] **Failure / Edge Case**: <System safely handles anomaly, no crash, logs error>

---

### ✍️ Test Execution & Hardware Sign-Off
- **Test Result**: [ ] PASS  [ ] FAIL
- **Firmware Version Tested**: 
- **Execution Date**: 
- **Tester**: 
- **Test Evidence / Notes**:
  *(Attach serial logs, terminal output, or LCD photo here)*

> [!IMPORTANT]
> This requirement MUST NOT be closed until all checkboxes above are checked and verified on physical hardware or test bench.
