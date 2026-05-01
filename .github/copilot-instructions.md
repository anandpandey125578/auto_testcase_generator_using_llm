# Auto Test Case Generator — Implementation Instructions

## 1. Objective
Build a web-based tool that:
1. Accepts BRD inputs (PDF and/or images)
2. Extracts and interprets requirements
3. Generates structured test cases in CSV format
4. Allows user review/edit of CSV
5. Generates automation code (Selenium or Playwright in Python) from the reviewed CSV

This is an MVP. Do NOT expand beyond defined scope.

---

## 2. Strict Scope (MVP)

### Supported Inputs
- PDF (text-based or scanned)
- Image files (JPG, PNG)
- Combination of PDF + images

### Supported Outputs
- Step 1: CSV test cases (mandatory intermediate output)
- Step 2: Automation code (ONLY after CSV upload)

### Test Coverage
- UI test scenarios
- API test scenarios

### Automation Frameworks
- Selenium (Python)
- Playwright (Python)

User must explicitly select framework before code generation.

---

## 3. Fixed CSV Schema (DO NOT MODIFY)

The generated CSV MUST strictly follow this schema:
TC_ID
Module
Title
Preconditions
Steps
Test_Data
Expected_Result
Type (UI/API)
Priority (High/Medium/Low)
Automation_Candidate (Yes/No)


### Rules:
- Column names must match EXACTLY
- Order must remain unchanged
- Validation must fail if schema mismatches

---

## 4. System Flow

### Step 1: File Upload
- User uploads:
  - PDF OR
  - Images OR
  - Both
- Validate file type
- Store locally (temporary)

---

### Step 2: Content Extraction
- PDFs:
  - Use `pdfplumber` (preferred) or `PyPDF2`
- Images:
  - Use OCR (`pytesseract`)

Output:
- Unified raw text

---

### Step 3: Test Case Generation (LLM)
- Input: Extracted text
- Output: Structured test cases in CSV format

Constraints:
- Must strictly follow CSV schema
- Must include both UI and API cases if applicable
- Avoid hallucinated modules not present in input

---

### Step 4: CSV Review UI
- Display generated CSV in editable table
- Allow:
  - Edit rows
  - Add rows
  - Delete rows
- Provide "Download CSV" option

---

### Step 5: CSV Upload (Reviewed Version)
- User uploads edited CSV

Validation:
- Schema check (strict)
- Reject if:
  - Missing columns
  - Extra columns
  - Wrong column order

---

### Step 6: Code Generation (LLM)
- Input: Validated CSV
- User selects:
  - Selenium (Python) OR
  - Playwright (Python)

Output:
- Structured automation code

Constraints:
- Modular code (not a single script dump)
- Readable and maintainable
- No unnecessary abstraction

---

## 5. UI Requirements (Django Templates Only)

### Pages

#### 1. Home Page
- File upload (PDF/Image)
- OpenAI API Key input (session only)
- Submit button

#### 2. CSV Review Page
- Editable table view
- Download CSV button
- Proceed to code generation

#### 3. Code Generation Page
- CSV upload
- Framework selection dropdown:
  - Selenium (Python)
  - Playwright (Python)
- Generate code button

#### 4. Output Page
- Display generated code
- Download option

---

## 6. API Key Handling
- User provides OpenAI API key via UI
- Store ONLY in session
- DO NOT persist in database or files

---

## 7. Project Structure
project/
│
├── app/
│ ├── views.py # Thin controllers
│ ├── urls.py
│
├── services/
│ ├── extraction_service.py # PDF + OCR logic
│ ├── llm_service.py # LLM calls
│ ├── csv_service.py # CSV validation & parsing
│ ├── codegen_service.py # Code generation logic
│
├── prompts/
│ ├── testcase_prompt.txt
│ ├── codegen_prompt.txt
│
├── utils/
│ ├── file_handler.py
│ ├── validators.py
│
├── templates/
│ ├── home.html
│ ├── review.html
│ ├── generate.html
│ ├── output.html
│
├── static/
│
└── manage.py


---

## 8. Design Principles

### Separation of Concerns
- Views → Only handle HTTP
- Services → Business logic
- Prompts → Isolated and reusable

---

### Error Handling
Must handle:
- Invalid file type
- OCR failure
- Empty extracted text
- CSV schema mismatch
- LLM failure

Return clear, user-friendly messages.

---

### Logging
- Log errors and major steps
- No sensitive data logging (API keys, file content)

---

## 9. LLM Responsibilities

### Test Case Generation
- Convert BRD text → structured test cases
- Maintain logical grouping by module
- Ensure clarity and completeness

---

### Code Generation
- Read CSV rows
- Convert each row into:
  - Test function
  - Assertions
  - Steps mapping

---

## 10. Non-Functional Constraints

- Local storage ONLY (no cloud storage)
- No authentication system
- No database required (optional for temp storage only)
- Must run locally via Django server
- Keep implementation simple and readable

---

## 11. Out of Scope (DO NOT IMPLEMENT)

- CI/CD integration
- Test execution engine
- Advanced reporting dashboards
- Multi-user support
- Authentication/login system
- Cloud deployment
- Versioning/history tracking
- AI fine-tuning or training

---

## 12. Acceptance Criteria

The system is complete when:

1. User uploads PDF/image → gets CSV
2. CSV is editable and downloadable
3. User uploads edited CSV → gets automation code
4. Both Selenium & Playwright code generation works
5. CSV schema validation is strict
6. Clear errors are shown for all failure cases

---

## 13. Key Implementation Notes

- Prioritize correctness over optimization
- Keep prompts deterministic and structured
- Avoid over-engineering
- Ensure reproducibility of outputs



## 14. Final Instruction

Do NOT:
- Add features beyond scope
- Modify CSV schema
- Introduce unnecessary abstractions

Focus on:
- Reliability
- Clarity
- Maintainability

---

## 15. Phase-Wise Development Plan

### Phase 1 — Project Skeleton + UI Flow
- Create Django project/app with template pages: Home, Review, Generate, Output
- Wire URLs and views (thin controllers)
- Local file handling utilities and temp storage
- Session storage for OpenAI API key only

### Phase 2 — Extraction Pipeline
- PDF text extraction via `pdfplumber` (fallback `PyPDF2`)
- Merge extracted text into a unified raw text payload
- Error handling for invalid files, OCR failure, empty text

### Phase 3 — Test Case Generation
- LLM prompt for structured test cases
- Enforce fixed CSV schema and ordering
- Generate CSV output and render in editable table
- Provide CSV download

### Phase 4 — CSV Review + Validation
- Editable table: add/edit/delete rows
- CSV upload for reviewed version
- Strict schema validation (columns, order, no extras)
- User-friendly error messages

### Phase 5 — Code Generation
- Framework selection: Selenium or Playwright (Python)
- LLM prompt to convert CSV rows into modular automation code (include image context when available)
- Output display + download
- Ensure readable, maintainable structure (no single script dump)

### Phase 6 — Hardening + Acceptance
- Add logs for major steps/errors (no sensitive data)
- End-to-end testing against acceptance criteria
- Fix edge cases (empty outputs, invalid CSV, prompt errors)

---
