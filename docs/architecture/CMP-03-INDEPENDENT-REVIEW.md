# INDEPENDENT ARCHITECTURE & SECURITY REVIEW: AIRA CMP-03

| Metadata | Detail |
| :--- | :--- |
| **Document ID** | `AIRA-REV-CMP-03-AUDIT` |
| **Target Review Document** | `docs/architecture/CMP-03-IMPLEMENTATION-PLAN.md` (`v1.0.0`) |
| **Repository & Branch** | `YayasanMandiriBersemi/aria-mochtar` (`main`) |
| **Baseline Commit** | `e1250ce` |
| **Review Roles** | Principal Software Architect, Senior Python Engineer, AI Systems Engineer, Application Security Auditor |
| **Review Mode** | `READ-ONLY INDEPENDENT AUDIT` |
| **Final Verdict** | **`CONDITIONALLY APPROVED`** |

---

## 1. Executive Verdict

Setelah melakukan pengujian kritis secara independen terhadap proposal **[CMP-03-IMPLEMENTATION-PLAN.md](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/docs/architecture/CMP-03-IMPLEMENTATION-PLAN.md)** dan membandingkannya baris demi baris dengan kode aktual `CMP-01` ([src/aira/config/](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/src/aira/config/settings.py)), kode aktual `CMP-02` ([src/aira/ports/channel.py](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/src/aira/ports/channel.py) dan [src/aira/interfaces/](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/src/aira/interfaces/router.py)), spesifikasi arsitektur hulu ([SYSTEM_ARCHITECTURE.md](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/docs/architecture/SYSTEM_ARCHITECTURE.md), [COMPONENT_OVERVIEW.md](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/docs/architecture/COMPONENT_OVERVIEW.md), [ARCHITECTURE_DECISIONS.md](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/docs/decisions/ARCHITECTURE_DECISIONS.md)), serta dokumentasi resmi **Google Gen AI Python SDK (`google-genai`)**, keputusan audit independen ini adalah:

> [!IMPORTANT]
> ### **STATUS: `CONDITIONALLY APPROVED` (Disetujui Bersyarat)**
> Fondasi makro arsitektur `CMP-03` sudah solid: mempertahankan pola *modular monolith*, memisahkan kontrak melalui `LLMProviderPort` (`ADR-007`), menegakkan prinsip *fail-closed* pada kredensial, dan menolak eksekusi tool otomatis sebelum `CMP-07` dibangun.
>
> **Namun**, audit ini menemukan **0 temuan `P0`**, **4 temuan `P1` (Major Functional / Integration / Cost Blockers)**, **4 temuan `P2` (Design & Security Gaps)**, dan **3 temuan `P3` (Minor Quality Improvements)** di dalam rencana `CMP-03-IMPLEMENTATION-PLAN.md` serta titik integrasinya dengan `CMP-02`. Implementasi kode **tidak boleh dimulai** sebelum syarat remediasi untuk keempat temuan `P1` (termasuk penyelesaian 3 utang `P1` pada `CMP-02`) dipenuhi sesuai urutan yang ditetapkan pada Bagian 10 dan Bagian 11 dokumen ini.

---

## 2. Architecture Strengths

Hal-hal berikut dalam `CMP-03-IMPLEMENTATION-PLAN.md` telah dirancang dengan benar dan layak dipertahankan:

1. **Kepatuhan terhadap *Modular Monolith* & Arah Dependensi Satu Arah (`SYSTEM_ARCHITECTURE.md` §7):**
   Pemisahan antara kontrak abstrak di `src/aira/ports/llm.py`, logika orkestrasi di `src/aira/core/`, dan implementasi konkret vendor di `src/aira/providers/gemini.py` mencegah *circular dependency* antara `interfaces`, `core`, dan `providers`.
2. **Rekonsiliasi Nama Port Tanpa Memutus `ADR-007` (`CMP-03-IMPLEMENTATION-PLAN.md#L67,L426-L441`):**
   Keputusan mendefinisikan `@runtime_checkable class LLMProviderPort(Protocol)` sebagai kontrak utama sesuai `ADR-007` dan menyediakan alias tipe `AIReasoningPort = LLMProviderPort` menjaga konsistensi dokumen hulu sekaligus kompatibilitas penamaan modul.
3. **Pemilihan SDK Resmi `google-genai` & Penolakan Framework Berat (`CMP-03-IMPLEMENTATION-PLAN.md#L536-L553`):**
   Melarang penggunaan paket warisan `google-generativeai` (yang sudah *deprecated*) serta menolak framework seperti `langchain`/`llamaindex` sesuai `TECH_STACK_DECISIONS.md` §7.
4. **Isolasi `SecretStr` dan Redaksi Berlapis (`CMP-03-IMPLEMENTATION-PLAN.md#L563-L566`):**
   Penggunaan `settings.redact_text()` (`src/aira/config/settings.py#L292-L321`) pada seluruh pesan exception SDK maupun teks output LLM memberikan *defense-in-depth* terhadap kebocoran tidak sengaja `GEMINI_API_KEY` dan `TELEGRAM_BOT_TOKEN`.
5. **Kejujuran Ruang Lingkup Tahap 1 (`CMP-03-IMPLEMENTATION-PLAN.md#L84-L98`):**
   Secara eksplisit menyatakan bahwa inferensi menggunakan layanan cloud eksternal (**Google Gemini Developer API**), tidak mengklaim memori persisten lintas-restart sebelum `CMP-06`, dan meniadakan registrasi tool (`config.tools = None`) sebelum `CMP-07` (Permission Engine) hadir.

---

## 3. P0 Findings (Critical Security or Correctness Blockers)

**Tidak ditemukan temuan `P0` (`0 P0 Findings`).**
Rancangan `CMP-03` tidak memperkenalkan celah *Remote Code Execution* (RCE), tidak membuka port jaringan publik, tidak melewati autentikasi `OwnerAuthGuard`, dan tidak mengeksekusi perintah shell atau sistem file.

---

## 4. P1 Findings (Major Functional, Integration, or Architectural Issues)

Berikut adalah **4 temuan `P1`** yang berdampak langsung pada kegagalan runtime, potensi ledakan biaya API, atau hilangnya pesan pengguna jika rencana `CMP-03` diimplementasikan apa adanya:

### `P1-CMP03-01`: Referensi ke API "Hantu" (`SlashCommand.ASK`, `CancelToken`, `coordinator.request_cancel()`) dan Kontradiksi Kontrak Pembatalan dengan Kode Aktual `CMP-02`
- **Referensi Dokumen Rencana:**
  - [CMP-03-IMPLEMENTATION-PLAN.md](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/docs/architecture/CMP-03-IMPLEMENTATION-PLAN.md#L169) (baris `169` & `210` — referensi `SlashCommand.ASK`)
  - [CMP-03-IMPLEMENTATION-PLAN.md](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/docs/architecture/CMP-03-IMPLEMENTATION-PLAN.md#L236) (baris `28`, `82`, `173`, `236`, `325`, `589`, `592`, `620`, `640` — referensi `CancelToken`, `coordinator.request_cancel()`, dan ekspektasi return `TurnResponse(cancelled=True)`)
- **Referensi Kode Aktual `CMP-02`:**
  - [src/aira/ports/channel.py](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/src/aira/ports/channel.py#L20-L30) (`class SlashCommand`)
  - [src/aira/interfaces/router.py](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/src/aira/interfaces/router.py#L208-L215) (`_TrackedTurn`) & [router.py](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/src/aira/interfaces/router.py#L311-L381) (`ActiveTurnCoordinator.handle_turn` & `handle_cancel`)
  - [src/aira/interfaces/cli_adapter.py](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/src/aira/interfaces/cli_adapter.py#L144-L154) (`CLIGateway.process_line`)
- **Analisis Masalah & Dampak Nyata:**
  1. **`SlashCommand.ASK` Tidak Ada di `CMP-02`:** Rencana baris `210` menyatakan `PromptContextBuilder` akan memeriksa `request.command == SlashCommand.ASK`. Di `src/aira/ports/channel.py#L20-L30`, anggota enum `SlashCommand` hanya `START`, `HELP`, `STATUS`, `CANCEL`, `TASKS`, `NOTES`, dan `BRIEFING`. Mengakses `SlashCommand.ASK` akan langsung menyebabkan crash `AttributeError` saat runtime.
  2. **`CancelToken` dan `coordinator.request_cancel()` Tidak Ada di `CMP-02`:** Rencana baris `236`, `325`, `592`, `620`, dan `640` (`AC-CMP03-08`) mengasumsikan `ActiveTurnCoordinator` membuat objek `CancelToken` dan memiliki method `request_cancel()`. Faktanya, `ActiveTurnCoordinator` (`src/aira/interfaces/router.py#L208-L381`) hanya menyimpan `asyncio.Task` di dalam `_TrackedTurn` dan membatalkan turn melalui method `await coordinator.handle_cancel(signal: CancellationSignal) -> CancelResult` (`#L337`).
  3. **Kontradiksi Semantik `asyncio.CancelledError` vs `TurnResponse(cancelled=True)`:**
     - Pada baris `174` dan `327`, rencana menyatakan `AiraCoreEngine.handle_turn()` me-re-raise `asyncio.CancelledError` saat dibatalkan.
     - Namun pada baris `329`, `620`, dan `640` (`AC-CMP03-08`), rencana menyatakan `ActiveTurnCoordinator.handle_turn()` akan mengembalikan `TurnResponse(cancelled=True)`.
     - Di kode aktual `src/aira/interfaces/router.py#L322-L335`, `ActiveTurnCoordinator.handle_turn()` **tidak menangkap `asyncio.CancelledError`**, melainkan membiarkan exception tersebut meledak keluar ke pemanggilnya!
     - Di jalur Telegram (`src/aira/interfaces/telegram_adapter.py#L718,L729-L730`), `_execute_turn()` menangkap `asyncio.CancelledError` dan me-re-raise-nya untuk menghentikan background task (sementara pesan konfirmasi `/cancel` sudah dikirim oleh `process_update` di baris `651-663`).
     - **Bahaya di Jalur CLI:** Di `CLIGateway.process_line()` (`src/aira/interfaces/cli_adapter.py#L144`), pemanggilan `response = await self._turn_handler.handle_turn(decision.request)` **sama sekali tidak memiliki blok `try ... except asyncio.CancelledError`**. Jika pengguna sedang menjalankan `aira chat` dan membatalkan turn yang sedang berjalan melalui perintah `aira cancel` (IPC) dari terminal kedua, `asyncio.CancelledError` akan meruntuhkan loop utama `run_chat_loop()` (`cli_adapter.py#L185`)!

---

### `P1-CMP03-02`: *Multiplicative Retry Storm* (`3 x 5 = 15` Request), Duplikasi Biaya Retry pada Timeout, dan Jebakan Satuan Milidetik pada SDK `google-genai`
- **Referensi Dokumen Rencana:**
  - [CMP-03-IMPLEMENTATION-PLAN.md](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/docs/architecture/CMP-03-IMPLEMENTATION-PLAN.md#L114) (baris `114` — timeout HTTP client config)
  - [CMP-03-IMPLEMENTATION-PLAN.md](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/docs/architecture/CMP-03-IMPLEMENTATION-PLAN.md#L187-L188) (baris `187-188` & `242-244` — nested `asyncio.wait_for` dan custom retry loop)
  - [CMP-03-IMPLEMENTATION-PLAN.md](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/docs/architecture/CMP-03-IMPLEMENTATION-PLAN.md#L585-L587) (baris `585-587` — retry pada `LLMTimeoutError` dan `429`/`503`)
- **Analisis Masalah & Dampak Nyata:**
  1. **Double-Retry (`3 x 5 = 15` Percobaan) dengan Built-in Retry `google-genai`:**
     Berdasarkan dokumentasi resmi SDK `google-genai` (`google.genai.types.HttpRetryOptions`), client HTTP bawaan SDK **sudah mengaktifkan automatic retry secara default** (`attempts=5` untuk HTTP status `408, 429, 500, 502, 503, 504`). Apabila `GeminiProviderAdapter` menambahkan loop retry manual (`max_retries=2` / `3` percobaan) tanpa menonaktifkan retry internal SDK (`HttpRetryOptions(attempts=1)`), maka saat terjadi error `429` atau `503`, sistem akan melakukan **hingga `3 x 5 = 15` percobaan HTTP** untuk satu pesan pengguna!
  2. **Jebakan Satuan Milidetik (`ms`) pada `google.genai.types.HttpOptions(timeout=...)`:**
     Berbeda dengan `httpx` yang menggunakan satuan detik (`float`), `google.genai.types.HttpOptions(timeout=...)` pada SDK `google-genai` menggunakan satuan **milidetik (`int`)**! Rencana baris `114` menyebutkan penerapan `timeout_seconds` (`45.0` atau `90.0`) ke HTTP client config. Jika implementor meneruskan `45` tanpa mengalikan `1000` (`45_000`), setiap panggilan ke Gemini API akan langsung gagal timeout dalam **45 milidetik**.
  3. **Tabrakan Timeout Identik antara `AiraCoreEngine` dan `GeminiProviderAdapter`:**
     Baris `187` mewajibkan `GeminiProviderAdapter.generate()` membungkus setiap panggilan `generate_content` dengan `asyncio.wait_for(..., timeout=request.timeout_seconds)`, sementara baris `242` mewajibkan `AiraCoreEngine` membungkus `self._provider.generate(llm_request)` dengan `asyncio.wait_for(..., timeout=llm_request.timeout_seconds)` menggunakan nilai `timeout_seconds` yang sama persis (`45.0s`). Akibatnya:
     - Jika percobaan pertama gagal pada detik ke-20 lalu melakukan backoff `1.5s` dan percobaan kedua membutuhkan `25s`, timeout luar di `AiraCoreEngine` akan memutus eksekusi pada detik ke-45 dengan menyuntikkan `asyncio.CancelledError` ke dalam adapter.
     - Membedakan antara `TimeoutError` (habis waktu) dan `CancelledError` (dibatalkan pengguna via `/cancel`) menjadi kacau apabila kedua lapis menggunakan `asyncio.wait_for` dengan batas waktu yang sama.
  4. **Duplikasi Biaya Token Akibat Retry pada `LLMTimeoutError`:**
     Baris `587` mengizinkan retry otomatis ketika terjadi `Request Timeout (asyncio.TimeoutError)`. Panggilan HTTP `POST generateContent` ke Gemini **bukanlah operasi idempoten terhadap kuota/biaya**: jika timeout terjadi di sisi klien (`ReadTimeout` setelah detik ke-45) padahal server Google sedang/sudah selesai men-generate ribuan token, melakukan retry otomatis akan memicu generasi kedua di server Google dan **menggandakan pemotongan kuota/biaya token (`2x`)**. Timeout lokal **tidak boleh** di-retry secara otomatis.

---

### `P1-CMP03-03`: Kelemahan `InMemoryTokenBudgetTracker` terhadap Konkurensi (Race Condition), Volatilitas Restart, dan Absennya `thoughts_token_count` pada Model Gemini 2.5
- **Referensi Dokumen Rencana:**
  - [CMP-03-IMPLEMENTATION-PLAN.md](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/docs/architecture/CMP-03-IMPLEMENTATION-PLAN.md#L112) (baris `112`, `170`, `238`, `246`, `610` — `InMemoryTokenBudgetTracker`)
  - [CMP-03-IMPLEMENTATION-PLAN.md](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/docs/architecture/CMP-03-IMPLEMENTATION-PLAN.md#L189) (baris `189` & `399-407` — `LLMUsageMetadata`)
- **Referensi Kode Aktual:**
  - [src/aira/config/settings.py](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/src/aira/config/settings.py#L99-L115) (`gemini_fast_model = "gemini-2.5-flash"`, `gemini_pro_model = "gemini-2.5-pro"`)
  - [src/aira/interfaces/telegram_adapter.py](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/src/aira/interfaces/telegram_adapter.py#L696-L713) (`_spawn_turn_task`)
- **Analisis Masalah & Dampak Nyata:**
  1. **Ilusi Batas Anggaran Harian di RAM (Process Restart & One-Shot CLI):**
     Karena `InMemoryTokenBudgetTracker` hanya hidup di memori proses Python (`RAM`), penghitung token otomatis ter-reset menjadi `0` setiap kali proses aplikasi di-restart, atau setiap kali pemilik menjalankan perintah CLI terpisah. Rencana pada baris `581` dan `610` tidak boleh mengklaim bahwa `DailyTokenBudgetExceededError` menegakkan batas biaya harian yang persisten; sebelum `CMP-06` (SQLite `token_usage_ledger`) hadir, komponen ini wajib dinamai dan didokumentasikan secara jujur sebagai **in-process session/daily token guard**.
  2. **Race Condition *Check-Then-Act* pada Request Konkuren:**
     Di `TelegramPollingGateway._spawn_turn_task()` (`src/aira/interfaces/telegram_adapter.py#L696-L698`), setiap pesan masuk di-spawn sebagai `asyncio.Task` konkuren tanpa antrean atau semaphore. Rencana `CMP-03` memeriksa anggaran di Langkah 4 (*pre-flight*, baris `238`), namun baru menambahkan token ke tracker di Langkah 7 (*post-flight*, baris `246`) setelah panggilan jaringan `generate_content` selesai (yang bisa memakan waktu 5–30 detik). Jika sisa anggaran tinggal `15.000` token dan ada 4 pesan masuk bersamaan, keempatnya akan melihat sisa `15.000` token saat *pre-flight*, lolos secara paralel ke Gemini API, dan melampaui batas anggaran. Tracker **wajib** menggunakan mekanisme **Pre-Flight Reservation** (`reserve(estimated_tokens)` sebelum panggilan jaringan, lalu `reconcile(reserved, actual_total_tokens)` di blok `finally`).
  3. **Absennya `thoughts_token_count` dan Penanganan `None` pada `usage_metadata` Gemini 2.5:**
     Model default di `CMP-01` adalah `gemini-2.5-flash` dan `gemini-2.5-pro`, yang secara native menggunakan *internal thinking tokens*. Pada SDK `google-genai`, `response.usage_metadata` memiliki field:
     - `prompt_token_count: int | None`
     - `candidates_token_count: int | None`
     - `thoughts_token_count: int | None` *(ditagih sebagai output token!)*
     - `cached_content_token_count: int | None`
     - `total_token_count: int | None`
     Selain itu, ketika respons diblokir oleh filter keamanan, `candidates_token_count` atau `total_token_count` sering kali bernilai **`None`** (bukan `0`). Kontrak `LLMUsageMetadata` (baris `399-407`) belum menyertakan `thoughts_tokens` / `cached_tokens`, dan rencana belum mewajibkan konversi `None`-safe (`int(val or 0)`), yang dapat memicu `pydantic.ValidationError` saat `usage_metadata` berisi `None`.

---

### `P1-CMP03-04`: Tiga Temuan `P1` pada `CMP-02` (Commit `e1250ce`) Wajib Diperbaiki *Sebelum* Integrasi `CMP-03`
- **Referensi Dokumen Rencana:**
  - [CMP-03-IMPLEMENTATION-PLAN.md](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/docs/architecture/CMP-03-IMPLEMENTATION-PLAN.md#L50-L59) & [#L677](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/docs/architecture/CMP-03-IMPLEMENTATION-PLAN.md#L677)
- **Referensi Kode Aktual `CMP-02`:**
  - **`P1-01`:** [src/aira/interfaces/telegram_adapter.py](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/src/aira/interfaces/telegram_adapter.py#L606-L624) & [#L649](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/src/aira/interfaces/telegram_adapter.py#L649)
  - **`P1-02`:** [pyproject.toml](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/pyproject.toml#L1-L33) & [src/aira/interfaces/cli_adapter.py](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/src/aira/interfaces/cli_adapter.py#L240)
  - **`P1-03`:** [src/aira/interfaces/telegram_adapter.py](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/src/aira/interfaces/telegram_adapter.py#L280-L293) & [#L556](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/src/aira/interfaces/telegram_adapter.py#L556)
- **Analisis Mengapa Tidak Boleh Ditunda ke Pasca-Phase 5:**
  Rencana `CMP-03` (baris `677`) mengizinkan perbaikan ketiga temuan `P1` `CMP-02` dilakukan *setelah* Phase 5 selesai. Ini tidak dapat diterima karena:
  1. **Interaksi Berbahaya antara `P1-01` dan Panggilan LLM Berdurasi Panjang:**
     Di `telegram_adapter.py#L649`, `self._offset_cursor.save_next_offset(update.update_id + 1)` dipanggil **sebelum** pengiriman balasan (`send_message` di baris `655`, `666`, `679`) dan **sebelum** task background `_spawn_turn_task` (baris `693`) menjalankan `AiraCoreEngine.handle_turn()`. Selain itu, `_is_duplicate_update()` (baris `606-607`) hanya memeriksa `self._seen_set` di RAM tanpa memeriksa `update.update_id < self._offset_cursor.load_next_offset()`.
     - *Catatan Transaksional Penting:* Pengakuan offset Telegram (`getUpdates` offset / `telegram_offset.json`), panggilan inferensi eksternal ke Gemini API, dan pengiriman pesan keluar (`sendMessage`) adalah tiga operasi terpisah yang **tidak mungkin dijadikan satu transaksi atomik** (*no distributed two-phase commit*). Sistem **tidak boleh menjanjikan *exactly-once delivery***.
     - Namun, sistem harus memperbaiki `_is_duplicate_update()` agar membandingkan `update_id < self._offset_cursor.load_next_offset()` saat startup (mencegah pemrosesan ulang update lama yang sudah di-commit), memindahkan penyimpanan offset untuk jalur sinkron (`CANCEL`, `UNAVAILABLE`, `COMMAND_LOCAL`) ke *setelah* `send_message`, dan mendokumentasikan secara jujur semantik *at-most-once* vs *at-least-once* untuk background turn task.
  2. **Ketiadaan Entrypoint CLI (`P1-02`):** Tanpa `[project.scripts]` (`aira = "aira.interfaces.cli_adapter:main"`) di `pyproject.toml`, pengguna tidak memiliki executable `aira` untuk menjalankan percakapan interaktif dengan `AiraCoreEngine`.
  3. **Inkonsistensi Konfigurasi Timeout (`P1-03`):** `HttpxTelegramTransport` (`telegram_adapter.py#L286`) menyimpan `self._poll_timeout_seconds` yang mati (dead attribute) dan dapat membingungkan pemeliharaan timeout ketika digabungkan dengan timeout `GeminiProviderAdapter`.

---

## 5. P2 Findings (Recommended Architectural & Security Improvements)

### `P2-CMP03-01`: *Orphaned Async Shutdown* — `AiraCoreEngine.aclose()` Tidak Dipanggil Saat Gateway Berhenti
- **Referensi:** [CMP-03-IMPLEMENTATION-PLAN.md](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/docs/architecture/CMP-03-IMPLEMENTATION-PLAN.md#L435-L437) & [#L485-L487](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/docs/architecture/CMP-03-IMPLEMENTATION-PLAN.md#L485-L487) vs [src/aira/interfaces/telegram_adapter.py](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/src/aira/interfaces/telegram_adapter.py#L814-L825) & [src/aira/interfaces/cli_adapter.py](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/src/aira/interfaces/cli_adapter.py#L156-L186).
- **Analisis:** `GeminiProviderAdapter` membuka sesi `httpx.AsyncClient` internal melalui `client.aio` pada SDK `google-genai` yang harus ditutup dengan `await self._client.aio.aclose()`. Namun, `InboundTurnHandler` (`src/aira/ports/channel.py#L172-L179`) tidak mendefinisikan `aclose()`, dan baik `ActiveTurnCoordinator`, `TelegramPollingGateway.stop()`, maupun `CLIGateway.run_chat_loop()` tidak memanggil `aclose()` pada `downstream_turn_handler`. Selain itu, `GeminiProviderAdapter` belum memiliki guard `_closed: bool` untuk menolak panggilan `generate()` baru setelah `aclose()` dipanggil.

### `P2-CMP03-02`: Penanganan `response.prompt_feedback` (Empty Candidates) dan `response.text is None` pada SDK `google-genai`
- **Referensi:** [CMP-03-IMPLEMENTATION-PLAN.md](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/docs/architecture/CMP-03-IMPLEMENTATION-PLAN.md#L189) & [#L219-L222](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/docs/architecture/CMP-03-IMPLEMENTATION-PLAN.md#L219-L222).
- **Analisis:**
  1. Pada SDK `google-genai`, apabila prompt masuk ditolak oleh filter keamanan tingkat prompt (`response.prompt_feedback.block_reason` terisi), maka `response.candidates` akan bernilai **`None` atau `[]`**. Jika `GeminiProviderAdapter` langsung mengakses `response.candidates[0].finish_reason`, kode akan crash dengan `IndexError` / `TypeError`.
  2. Properti `response.text` pada `GenerateContentResponse` dapat bernilai **`None`** (misalnya ketika seluruh `max_output_tokens` habis dipakai oleh `thoughts_token_count` pada Gemini 2.5 sehingga tidak ada part teks yang dihasilkan, atau ketika kandidat diblokir `SAFETY`). Karena `LLMGenerationResult.text` didefinisikan sebagai `str = Field(default="")` (baris `416`), meneruskan `text=response.text` saat bernilai `None` akan memicu `pydantic.ValidationError`.

### `P2-CMP03-03`: Keterbatasan Keamanan Tag XML `<untrusted_external_data>` dan Ketidaksinkronan Batas Karakter (`32.000` vs `64.000`)
- **Referensi:** [CMP-03-IMPLEMENTATION-PLAN.md](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/docs/architecture/CMP-03-IMPLEMENTATION-PLAN.md#L212-L214) & [#L567](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/docs/architecture/CMP-03-IMPLEMENTATION-PLAN.md#L567) vs [src/aira/interfaces/router.py](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/src/aira/interfaces/router.py#L27) (`MAX_INPUT_TEXT_LENGTH = 32_000`).
- **Analisis:**
  1. **Inkonsistensi Batas Input:** `CommandRouter` di `CMP-02` (`router.py#L27,L104`) menolak semua pesan `> 32.000` karakter, sedangkan `PromptContextBuilder` di `CMP-03` (baris `212`) menghitung batas `max_input_chars = 16.000 * 4 = 64.000` karakter. Input berukuran `32.001`–`64.000` karakter tidak akan pernah bisa mencapai `PromptContextBuilder` kecuali konstanta di `CommandRouter` diselaraskan dengan konfigurasi `settings.max_input_tokens_per_turn`.
  2. **Bypass XML Escaping Sederhana & Keterbatasan Fundamental Delimiter XML:** Rencana baris `567` hanya menyebutkan penggantian literal `</untrusted_external_data>`. Input berbahaya dapat menggunakan variasi case/whitespace seperti `</UNTRUSTED_EXTERNAL_DATA >` atau menyisipkan tag pembuka `<untrusted_external_data>` palsu. Fungsi `wrap_untrusted_data()` harus melakukan sanitasi karakter `<` dan `>` (atau regex case-insensitive pada seluruh tag delimiter) dan men-sanitize atribut `source="..."`. Lebih penting lagi, dokumen arsitektur wajib menegaskan bahwa **tag XML hanyalah pemisah konteks heuristik dan tidak pernah dapat mencegah *prompt injection* secara deterministik**.

### `P2-CMP03-04`: Aturan Pemilihan `ModelTier.FAST` vs `ModelTier.PRO` Belum Spesifik (`FR-CORE-04`)
- **Referensi:** [CMP-03-IMPLEMENTATION-PLAN.md](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/docs/architecture/CMP-03-IMPLEMENTATION-PLAN.md#L110) & [#L171](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/docs/architecture/CMP-03-IMPLEMENTATION-PLAN.md#L171).
- **Analisis:** Rencana menyebutkan `AiraCoreEngine` memilih `ModelTier.PRO` ketika *"explicitly requested or when input complexity exceeds configurable threshold"*, namun tidak mendefinisikan cara pengguna memintanya (mengingat `CommandRouter` menolak slash command di luar whitelist) maupun rumus/ambang batas kompleksitasnya. Tanpa spesifikasi yang tegas, perilaku pemilihan model menjadi ambigu.

---

## 6. P3 Findings (Optional / Minor Quality Improvements)

1. **`P3-CMP03-01` — Kesalahan Indentasi (Syntax Error) pada Definisi `LLMGenerationRequest`:**
   - Pada [CMP-03-IMPLEMENTATION-PLAN.md](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/docs/architecture/CMP-03-IMPLEMENTATION-PLAN.md#L395) baris `395`, deklarasi field `     estimated_input_tokens: int = Field(default=0, ge=0)` menjorok 5 spasi (bukan 4 spasi), yang akan memicu `IndentationError` jika disalin langsung.
2. **`P3-CMP03-02` — Visibilitas Status `CMP-03` pada Perintah `/status`:**
   - Pada [src/aira/interfaces/router.py](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/src/aira/interfaces/router.py#L240-L252), `ActiveTurnCoordinator.get_status_snapshot()` hanya menampilkan `"reasoning_core_attached": bool`. Menambahkan hook opsional agar `/status` menampilkan nama model aktif (`gemini_fast_model` / `gemini_pro_model`) dan pemakaian token sesi saat ini akan meningkatkan observabilitas secara signifikan.
3. **`P3-CMP03-03` — Spesifikasi Eksplisit `TurnResponse.parse_mode`:**
   - Pada [CMP-03-IMPLEMENTATION-PLAN.md](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/docs/architecture/CMP-03-IMPLEMENTATION-PLAN.md#L223), rencana perlu menetapkan secara eksplisit bahwa `ResponseHandler` mengeset `parse_mode="Markdown"` (atau `None` secara default) karena `TelegramDeliveryAdapter` (`src/aira/interfaces/telegram_adapter.py#L510-L530`) sudah mendukung fallback otomatis ke *plain text* apabila terdapat simbol Markdown yang tidak seimbang dari output LLM.

---

## 7. Security Assessment

| Area Audit Keamanan | Evaluasi Kritis | Status |
| :--- | :--- | :--- |
| **Manajemen Kredensial (`GEMINI_API_KEY`)** | Diekstrak melalui `.get_secret_value()` hanya di dalam konstruktor private `GeminiProviderAdapter`. Wajib memastikan objek `genai.Client` tidak pernah di-serialize atau di-log. | **kuat (`Pass`)** |
| **Redaksi Rahasia pada Log & Output** | Seluruh pesan error dari `google.genai.errors.APIError` / `httpx` dan seluruh teks kandidat LLM melewati `settings.redact_text()`. | **Kuat (`Pass`)** |
| **Ketahanan terhadap *Prompt Injection*** | `PromptContextBuilder.wrap_untrusted_data()` mengenkapsulasi data eksternal dengan tag `<untrusted_external_data>`, namun **tidak boleh dianggap sebagai pencegah *prompt injection* yang absolut** (`P2-CMP03-03`). Pertahanan utama yang sebenarnya di `CMP-03` adalah **ketiadaan registrasi tool (`config.tools = None`)**, sehingga model sama sekali tidak memiliki kapabilitas mengeksekusi aksi eksternal. | **Bersyarat (`Needs P2-CMP03-03 Fix`)** |
| **Privasi Log (`MEMORY_PRIVACY_POLICY.md`)** | Rencana melarang pencatatan teks mentah prompt (`raw_text`) maupun teks balasan LLM ke dalam log standar (`INFO`/`WARNING`/`ERROR`), hanya mencatat metadata (`trace_id`, `model_id`, jumlah token, latensi). | **Kuat (`Pass`)** |
| **Pengendalian Kuota & Denial of Wallet (`FR-LLM-02`)** | Batas token per giliran (`16.000` token) dicegah sebelum panggilan jaringan. Namun, penghitung harian di RAM rentan terhadap *race condition* konkurensi dan *multiplicative retry* (`P1-CMP03-02`, `P1-CMP03-03`). | **Bersyarat (`Needs P1 Fixes`)** |

---

## 8. Performance & Reliability Assessment

1. **Non-Blocking Async I/O (`client.aio`):**
   Keputusan menggunakan `await client.aio.models.generate_content(...)` sudah tepat karena tidak memblokir *event loop* utama yang melayani long polling Telegram dan server Unix Domain Socket IPC.
2. **Overhead Estimasi Token Lokal vs `count_tokens` API:**
   Keputusan menggunakan estimator lokal ($\lceil \text{len(utf8\_bytes)} / 3.5 \rceil$) di `PromptContextBuilder` menghindari penalti latensi tambahan sebesar `200ms–500ms` per giliran yang akan terjadi jika memanggil endpoint `client.aio.models.count_tokens()` sebelum setiap `generate_content()`. Untuk teks bahasa Indonesia dan kode sumber Python, rasio `3.5 bytes/token` cukup konservatif sebagai *pre-flight guard*, selama jumlah token aktual dari `usage_metadata.total_token_count` tetap direkonsiliasi pasca-respons.
3. **Alokasi Anggaran Timeout & Retry:**
   Saat ini terdapat konflik antara timeout luar (`AiraCoreEngine`) dan timeout dalam (`GeminiProviderAdapter`) yang bernilai sama (`45.0s` untuk `FAST`, `90.0s` untuk `PRO`). Timeout harus dibagi menjadi **Per-Attempt HTTP Timeout** (mis. `30.0s` / `30_000 ms` untuk `FAST` dan `60.0s` / `60_000 ms` untuk `PRO`) dan **Overall Turn Deadline** di `AiraCoreEngine` (mis. `65.0s` untuk `FAST` dan `125.0s` untuk `PRO`) agar retry transien memiliki ruang waktu yang jelas tanpa memicu pembatalan prematur.

---

## 9. CMP-02 Dependency & Integration Assessment

Integrasi antara `CMP-02` dan `CMP-03` bertumpu pada empat kontrak di [src/aira/ports/channel.py](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/src/aira/ports/channel.py) dan [src/aira/interfaces/router.py](file:///Users/jahseyamochtarmawardi/Downloads/aira-mochtar/src/aira/interfaces/router.py):

1. **`InboundTurnHandler.handle_turn(request: InboundUserRequest) -> TurnResponse` (`channel.py#L172-L179`):**
   Signature method antara `ActiveTurnCoordinator` (`router.py#L332`) dan `AiraCoreEngine` sudah **100% kompatibel**.
2. **`InboundUserRequest` (`channel.py#L49-L65`):**
   Ketika pengguna mengirim pesan biasa, `CommandRouter.route()` (`router.py#L179-L189`) menghasilkan `InboundUserRequest` dengan `command=None`, `command_args=""`, dan `normalized_text=trimmed`. `PromptContextBuilder` di `CMP-03` harus membaca `request.normalized_text` (dan **menghapus referensi ke `SlashCommand.ASK`** yang tidak ada).
3. **Propagasi Pembatalan di `ActiveTurnCoordinator` (`router.py#L311-L335`) & `CLIGateway` (`cli_adapter.py#L144`):**
   - Saat `ActiveTurnCoordinator.handle_cancel()` (`router.py#L365`) memanggil `entry.task.cancel()`, task yang sedang menjalankan `handle_turn()` menerima `asyncio.CancelledError`.
   - `AiraCoreEngine.handle_turn()` **wajib tidak menelan `asyncio.CancelledError`** (wajib di-re-raise setelah membersihkan reservasi anggaran token di blok `finally`).
   - `CLIGateway.process_line()` (`cli_adapter.py#L144`) perlu menangkap `asyncio.CancelledError` dan menampilkan pesan pembatalan ke konsol agar sesi interaktif `aira chat` tidak keluar/crash ketika dibatalkan lewat IPC.
4. **Ketergantungan pada Penyelesaian 3 Temuan `P1` `CMP-02`:**
   Sebagaimana diuraikan pada `P1-CMP03-04`, menghubungkan `CMP-03` ke `TelegramPollingGateway` sebelum `P1-01`, `P1-02`, dan `P1-03` diperbaiki akan mengekspos panggilan Gemini API berbayar pada risiko *silent message loss* saat restart dan ketiadaan binary CLI `aira`.

---

## 10. Required Remediation (Syarat Wajib Sebelum/Saat Implementasi)

Agar status `CONDITIONALLY APPROVED` terpenuhi pada saat implementasi, seluruh poin berikut **wajib** diterapkan:

1. **Remediasi `R-01` (Perbaiki 3 Utang `P1` pada `CMP-02` Terlebih Dahulu — Menutup `P1-CMP03-04`):**
   - **`P1-01` (`src/aira/interfaces/telegram_adapter.py`):** Perbarui `_is_duplicate_update(update_id)` agar mengembalikan `True` jika `update_id in self._seen_set or update_id < self._offset_cursor.load_next_offset()`. Pindahkan penyimpanan `save_next_offset(update.update_id + 1)` setelah pengiriman pesan selesai untuk jalur sinkron, dan dokumentasikan bahwa antara pengiriman pesan Telegram, eksekusi Gemini API, dan penyimpanan offset lokal berlaku semantik *at-most-once* / *at-least-once* yang jujur (bukan *atomic exactly-once*).
   - **`P1-02` (`pyproject.toml` & `src/aira/interfaces/cli_adapter.py`):** Tambahkan entrypoint fungsi `main()` di `cli_adapter.py` dan daftarkan `[project.scripts]` `aira = "aira.interfaces.cli_adapter:main"` di `pyproject.toml`.
   - **`P1-03` (`src/aira/interfaces/telegram_adapter.py`):** Hapus atribut duplikat `_poll_timeout_seconds` yang tidak digunakan pada `HttpxTelegramTransport` sehingga konfigurasi polling timeout memiliki satu sumber kebenaran (*single source of truth*).
2. **Remediasi `R-02` (Bersihkan Kontrak Integrasi `CMP-02` $\leftrightarrow$ `CMP-03` — Menutup `P1-CMP03-01`):**
   - Hapus seluruh referensi ke `SlashCommand.ASK`, `CancelToken`, dan `coordinator.request_cancel()`.
   - Gunakan `request.normalized_text` di `PromptContextBuilder`.
   - Pastikan `AiraCoreEngine.handle_turn()` selalu me-re-raise `asyncio.CancelledError` (tidak pernah menelannya menjadi respons sukses palsu), dan tambahkan penanganan `except asyncio.CancelledError` yang aman pada `CLIGateway.process_line()` (`src/aira/interfaces/cli_adapter.py#L144`) atau `ActiveTurnCoordinator`.
3. **Remediasi `R-03` (Kendalikan Retry, Satuan Timeout `ms`, dan Larang Retry pada Timeout — Menutup `P1-CMP03-02`):**
   - Matikan automatic retry bawaan SDK `google-genai` dengan menyetel `HttpRetryOptions(attempts=1)` di dalam `types.HttpOptions` (sehingga retry dikendalikan penuh di satu tempat oleh `GeminiProviderAdapter` maksimal `2` retry / `3` total percobaan), **atau** delegasikan sepenuhnya ke `HttpRetryOptions(attempts=3)` tanpa loop retry ganda.
   - Konversikan nilai timeout ke **milidetik (`int(attempt_timeout_seconds * 1000)`)** saat mengonfigurasi `types.HttpOptions(timeout=...)`.
   - Pisahkan `per_attempt_timeout_seconds` (mis. `30.0s` FAST / `60.0s` PRO) dari `turn_deadline_seconds` di `AiraCoreEngine`.
   - **Larang retry otomatis pada `LLMTimeoutError`** untuk mencegah penagihan token ganda pada request yang masih berjalan di server Google; batasi retry hanya untuk HTTP `429`, `502`, `503`, `504`, dan kegagalan koneksi tingkat soket (`ConnectError`).
4. **Remediasi `R-04` (Reservasi Anggaran Pre-Flight & Akuntansi `thoughts_token_count` — Menutup `P1-CMP03-03` & `P2-CMP03-02`):**
   - Implementasikan metode **Pre-Flight Reservation** (`reserve(estimated_tokens)` sebelum panggilan jaringan dan `reconcile(reserved_tokens, actual_tokens)` / `release(reserved_tokens)` di blok `finally`) pada `InMemoryTokenBudgetTracker` agar bebas *race condition* saat menerima request konkuren.
   - Tambahkan field `thoughts_tokens: int = 0` dan `cached_tokens: int = 0` pada `LLMUsageMetadata`, gunakan ekstraksi `None`-safe (`int(getattr(usage, "prompt_token_count", 0) or 0)`), periksa `response.prompt_feedback` sebelum mengakses `response.candidates`, dan tangani `response.text is None` dengan aman (`response.text or ""`).
   - Dokumentasikan secara eksplisit pada kode dan respons `/status` bahwa `InMemoryTokenBudgetTracker` adalah pembatas anggaran tingkat proses (*in-process memory guard*) yang ter-reset saat restart hingga `CMP-06` (SQLite) diimplementasikan.
5. **Remediasi `R-05` (Shutdown Lifecycle, Sanitasi XML, & Keselarasan Input Bound — Menutup `P2-CMP03-01`..`04`):**
   - Hubungkan pemanggilan `await core_engine.aclose()` (yang memanggil `await self._client.aio.aclose()`) ke jalur penutupan `TelegramPollingGateway.stop()` dan akhir loop `CLIGateway.run_chat_loop()`.
   - Perkuat `PromptContextBuilder.wrap_untrusted_data()` dengan regex case-insensitive untuk seluruh variasi tag `<untrusted_external_data>` / `</untrusted_external_data>`, dan selaraskan batas karakter antara `CommandRouter` dan `PromptContextBuilder`.
   - Tetapkan aturan pemilihan `ModelTier` secara deterministik: selalu gunakan `ModelTier.FAST` secara default kecuali diminta secara eksplisit melalui argumen/konfigurasi yang terdefinisi jelas.

---

## 11. Recommended Implementation Order

Untuk meminimalkan risiko regresi dan memastikan fondasi gateway benar-benar bersih sebelum mesin penalaran AI dipasang, implementasi **wajib** mengikuti urutan fase berikut:

1. **Phase 0 — Remediation Patch `CMP-02` (`P1-01`, `P1-02`, `P1-03` & CLI Cancellation Guard):**
   - Perbaiki deduplikasi offset pasca-restart dan urutan `save_next_offset` di `src/aira/interfaces/telegram_adapter.py`.
   - Hapus atribut timeout duplikat di `HttpxTelegramTransport`.
   - Tambahkan entrypoint `[project.scripts]` (`aira = ...`) di `pyproject.toml` dan fungsi `main()` di `src/aira/interfaces/cli_adapter.py`, serta tangani `asyncio.CancelledError` di `CLIGateway.process_line()` dan hook `aclose()`.
   - Pastikan seluruh unit test `CMP-01` dan `CMP-02` lulus (`pytest -v`).
2. **Phase 1 — Dependencies & AI Reasoning Port (`src/aira/ports/llm.py` & `src/aira/core/exceptions.py`):**
   - Tambahkan `google-genai>=1.0.0,<2.0.0` ke `pyproject.toml`.
   - Implementasikan `LLMProviderPort` (`AIReasoningPort`), `LLMUsageMetadata` (termasuk `thoughts_tokens` dan `cached_tokens`), `LLMGenerationRequest`, `LLMGenerationResult`, serta hierarki `CoreEngineError` / `LLMProviderError`.
3. **Phase 2 — Persona, Context Builder, Budget Tracker & Response Handler (`src/aira/core/`):**
   - Implementasikan `InMemoryTokenBudgetTracker` dengan mekanisme *pre-flight token reservation* (`reserve` / `reconcile` / `release`).
   - Implementasikan `PersonaSystemInstructionManager` (`src/aira/core/persona.py`).
   - Implementasikan `PromptContextBuilder` (`src/aira/core/context_builder.py`) tanpa referensi `SlashCommand.ASK` dan dengan sanitasi XML yang ketat.
   - Implementasikan `ResponseHandler` (`src/aira/core/response_handler.py`) dengan `settings.redact_text()` dan penanganan `prompt_feedback` / `finish_reason`.
4. **Phase 3 — Gemini Provider Adapter (`src/aira/providers/gemini.py`):**
   - Implementasikan `GeminiProviderAdapter` menggunakan `client.aio.models.generate_content`, konversi timeout ke milidetik (`int(timeout_s * 1000)`), deaktivasi double-retry (`HttpRetryOptions(attempts=1)`), *None-safe* ekstraksi metadata & teks, larangan retry pada timeout/permanent error, serta `await client.aio.aclose()`.
5. **Phase 4 — Aira Core Orchestrator (`src/aira/core/engine.py`) & Wiring Gateway:**
   - Implementasikan `AiraCoreEngine(InboundTurnHandler)` dengan propagasi `asyncio.CancelledError` yang murni dan integrasi lifecycle `aclose()`.
6. **Phase 5 — Offline Verification Suite (`tests/test_core_engine.py`) & As-Built Docs:**
   - Tulis pengujian unit dan integrasi 100% offline yang memverifikasi seluruh skenario normal, reservasi anggaran konkuren, blokir keamanan (`prompt_feedback` & `candidate.finish_reason`), pembatalan di tengah giliran, redaksi rahasia, dan ketiadaan double-retry.

---

## 12. Final Approval Status

**KEPUTUSAN AKHIR: `CONDITIONALLY APPROVED`**

### Alasan Teknis Keputusan
Rancangan arsitektur `CMP-03` telah memenuhi struktur modularitas, pemisahan port (`LLMProviderPort` / `InboundTurnHandler`), serta prinsip dasar keamanan (`SecretStr` isolation, `redact_text()`, dan ketiadaan akses eksekusi tool otomatis). Oleh karena itu, arsitektur ini **tidak ditolak (`NOT REJECTED`)** karena tidak memerlukan perombakan ulang struktur paket.

Namun, proposal ini **tidak dapat diberikan status `APPROVED` tanpa syarat** karena empat temuan `P1` (`P1-CMP03-01` s/d `P1-CMP03-04`) merupakan cacat teknis nyata yang akan menyebabkan:
1. `AttributeError` pada `SlashCommand.ASK` dan crash `CancelledError` pada loop CLI (`P1-CMP03-01`),
2. Kegagalan timeout `45ms` akibat satuan milidetik pada `HttpOptions` serta badai retry `15x` akibat tumpang-tindih dengan retry internal SDK `google-genai` (`P1-CMP03-02`),
3. Kebocoran batas kuota token pada request paralel dan `ValidationError` saat `usage_metadata` bernilai `None` pada model thinking Gemini 2.5 (`P1-CMP03-03`), serta
4. Risiko kehilangan pesan Telegram saat restart apabila `CMP-03` diintegrasikan sebelum ketiga temuan `P1` pada `CMP-02` diperbaiki (`P1-CMP03-04`).

Dengan menerapkan **Remediasi `R-01` s/d `R-05`** sesuai urutan **Phase 0 s/d Phase 5** di atas, tim engineering diizinkan melanjutkan ke tahap implementasi.
