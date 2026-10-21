# Frontend Manual Verification Checklist

Use this checklist to verify all redesigned screens and integrated flows between the React frontend and FastAPI backend.

---

## 1. Bilingual Language Toggle Persistence
- [ ] Open `http://localhost:5173/`.
- [ ] Click the language toggle pill: switch from **English** to **മലയാളം**.
- [ ] Verify all UI labels, helpers, placeholders, and buttons on the report form switch to natural Malayalam.
- [ ] Refresh the browser (`F5`).
- [ ] **Expected:** Language choice persists as `ml` in `localStorage('lang')` across page refreshes and navigations.
- [ ] Toggle back to **English**.

---

## 2. Public Report Form (`/`)
### A. Form & Panchayat Removal Verification
- [ ] Confirm there is **no panchayat dropdown, field, or label** on the form. District is the sole location selector.
- [ ] Select Category: e.g. "Neglect" (or "Physical abuse").
- [ ] Enter Landmark: e.g. "Near Central Bus Station".
- [ ] Select District: "Thiruvananthapuram" (dynamically populated from `/api/locations/districts`).

### B. Speech-to-Text Voice Input Box
- [ ] In the dashed voice box, select language (`ml-IN` or `en-IN`).
- [ ] Click "Speak instead of typing".
- [ ] Allow microphone permission when prompted by the browser.
- [ ] Speak a phrase: verify recognized text appends to the "What did you see?" textarea.
- [ ] Verify helper text: *"Voice-to-text is not perfect. Please check and edit the text before you submit."*
- [ ] Click the button again to stop recording.
- [ ] Test without voice: type directly into textarea (at least 10 characters).

### C. Approximate Time
- [ ] Fill in "Approximate time": e.g. "around 5:30 PM".
- [ ] Verify this is appended cleanly to the description sent to the backend.

### D. Optional Photo Picker
- [ ] Click "Choose from gallery" (or "Take photo") and select an image file.
- [ ] Verify image preview appears with a "Remove photo" button.
- [ ] Verify the red notice: *"Do not photograph a child."*
- [ ] Verify the note: *"Photos are not uploaded in this demo."*
- [ ] Attempt submission without checking the confirmation checkbox -> verify prompt to confirm.
- [ ] Check *"I confirm this photo does not show a child."*
- [ ] Click "Remove photo" -> preview is removed and file inputs cleared.

### E. Immediate Danger (Yes / No / Not sure)
- [ ] Verify three segmented buttons: **Yes**, **No**, **Not sure** (single choice required).
- [ ] Select **Yes** -> button highlighted in danger red (`is_urgent: true`).
- [ ] Select **No** or **Not sure** -> button highlighted in teal (`is_urgent: false`).
- [ ] Verify "Reporter's answer to immediate danger: <selection>" is appended to narrative for the officer.

### F. Approximate Area Geolocation Consent
- [ ] Toggle checkbox: *"Share my approximate area (about 1 km) with the district child protection officer."*
- [ ] Allow geolocation when prompted. Verify coordinates are validated against Kerala boundary box (lat 8.0-12.8, lng 74.8-77.6) and rounded to 2 decimals (~1 km).
- [ ] Uncheck box -> verify coordinates cleared (`location_consent: false`).

### G. Submission & Confirmation Card
- [ ] Click "Submit report".
- [ ] Verify calm confirmation card displays:
  - Unique report ID (e.g. `KAR-XXXXXXXX`).
  - One-time reporter token with warning: *"Save this now. It cannot be shown again."*
  - "Copy Token" button -> click it and verify "Copied to clipboard!".
  - Restyled "Request a callback" button -> click it, verify callback requested status.
- [ ] Verify token is stored only in `sessionStorage` (never in `localStorage`).

---

## 3. Emergency Helpline Simulation (`/emergency`)
- [ ] Click the red **"Emergency help"** button from `/` or `/login`.
- [ ] **State 1: Idle**
  - Verify `DemoNotice` with dashed gold border.
  - Dark `Hero` ("Karuthal · Care Before Crisis" / "Emergency help" / "Tap once to call the nearest women helpline...").
  - Nearest District selector (defaults or remembers `localStorage`).
  - Red "Start call" button with inline SVG phone icon.
  - "Use phone dialer instead" plain `tel:112` link with caption "Opens your phone dialer".
- [ ] **State 2: Connecting**
  - Click "Start call".
  - Verify emergency call event is logged to backend (`POST /api/emergency`).
  - Dark teal full card with pulsing gold ring around phone icon.
  - "Connecting you to the nearest helpline..." with timer `00:00` and red "End call" button.
- [ ] **State 3: Connected (demo)**
  - Transitions automatically after ~2 seconds.
  - Monospace running timer (`00:01`, `00:02`, `00:03`...).
  - Tip in gold: *"Tell them where you are and what is happening."*
- [ ] **State 4: Ended**
  - Click "End call".
  - White card with teal check circle icon.
  - "Call ended" with final duration (e.g. `Duration 00:05`).
  - Buttons: "Write a report now" (goes to `/`) and "Back to home".

---

## 4. Officer Authentication (`/login`)
- [ ] Navigate to `/login`.
- [ ] Verify dark teal background (`--teal-950`).
- [ ] Verify arch-shaped hero (inline SVG with gold arch outline and person icon).
- [ ] Verify language toggle at top right.
- [ ] Verify demo credentials password is **NOT displayed** on the page.
- [ ] Test "Show" / "Hide" password toggle.
- [ ] Click "Forgot password?" -> verify non-blocking message: *"Officer accounts are issued by your department. Contact your administrator."*
- [ ] Test quick navigation buttons: "Report a concern" and red-tinted "Emergency help".
- [ ] Enter valid officer credentials: `DCPU-TVM-01` and demo password.
- [ ] Click "Sign in" -> redirects to `/dashboard`.

---

## 5. Officer Dashboard (`/dashboard`) & Panchayat Removal
- [ ] Verify metrics grid: Total Cases, Pending Review, Urgent Concerns, Solved Cases.
- [ ] Verify **Emergency & Helpline Events table**: displays the emergency call initiated in step 3.
  - Click "Acknowledge" on active emergency call -> status updates to `Acknowledged`.
- [ ] Verify **District Reports table**:
  - Confirm **NO Panchayat column** exists in the table header or rows.
  - Displays Case ID, Category, Urgency badge (red for Urgent), Location Status, Status, and Actions.
  - Verify newly submitted report from step 2 is listed.
- [ ] Verify **District Case Map**:
  - Plotted pins for consented reports.
  - Click pin -> verify quick preview card shows Case ID and Status (confirm **NO panchayat** in map preview).
- [ ] Click "Mark Solved" on a pending case -> state updates to `Solved`.

---

## 6. Case Detail (`/case/:id`)
- [ ] Open case from dashboard table or direct URL.
- [ ] Verify restyled theme cards (teal header, gold accents).
- [ ] Verify **Case Location Intelligence**:
  - Confirm **NO Panchayat label or field**. Only District, Citizen Consent, Landmark, and approximate coordinates.
- [ ] Verify **Simulated Call Panel**:
  - Retains prominent *"SIMULATED PROTOTYPE"* banner.
  - Click "Call Reporter (Simulated)" -> initiates session.
  - Click "Accept Call", duration timer runs, click "End Call".
- [ ] Click "Generate AI Decision Support Summary" -> displays advisory summary and checklist.
- [ ] Verify Chronological Case Audit Trail.

---

## 7. Cross-District Authorization Enforcement (403)
- [ ] Click "Sign Out" in officer header.
- [ ] Log in as Kollam officer: `DCPU-KLM-01`.
- [ ] Attempt to directly access a Thiruvananthapuram case URL: `/case/KAR-...`.
- [ ] **Expected:** Access denied (403 Forbidden); UI displays message indicating resource is outside assigned district.

---

## 8. Mobile (390px) & Desktop Responsive Inspection
- [ ] At 390px mobile viewport: public pages (`/`, `/emergency`, `/login`) display cleanly within 440px max-width centered column with comfortable padding, no horizontal scrolling.
- [ ] At 1280px+ desktop viewport: public column remains centered (max-width 440px, does not stretch), while Officer Dashboard and Case Detail expand comfortably across 1140px container.
