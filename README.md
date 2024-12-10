# LangGraph

## Gambaran Umum

Repository ini adalah pembelajaran yang dirancang untuk menunjukkan prinsip dan kemampuan LLM berbasis grafik dalam pengelolaan tugas dan eksekusi sistem. Repository ini menyediakan berbagai sumber daya, dokumentasi, dan contoh penggunaan LangGraph untuk mengelola alur kerja kompleks yang melibatkan banyak agen AI, perutean tugas, ringkasan informasi, dan paralelisasi.

Tujuan utamanya adalah memberikan cara intuitif untuk mengelola alur tugas AI yang dinamis dengan memanfaatkan struktur grafik, mendukung komunikasi antar komponen secara mulus, serta menyediakan fitur seperti penanganan breakpoint dinamis dan supervisi.

## Fitur Utama

- **Manajemen Agen**: Mendefinisikan dan mengontrol agen individual dalam sistem berbasis grafik.
- **Perutean Tugas**: Merutekan tugas secara dinamis antar agen sesuai dengan kapabilitasnya.
- **Paralelisasi**: Menjalankan tugas secara bersamaan untuk mengoptimalkan performa.
- **Ringkasan Informasi**: Mengkondensasi informasi secara otomatis untuk efisiensi pemrosesan.
- **Breakpoint Dinamis**: Mengimplementasikan breakpoint untuk menghentikan dan melanjutkan tugas sesuai kebutuhan.
- **Supervisi**: Memantau dan mengatur alur tugas selama eksekusi.
- **Ekstensibilitas**: Memungkinkan perluasan atau penyesuaian komponen dengan mudah menggunakan Python.

## Struktur Repository

Berikut adalah struktur utama repository ini:

```bash
.
├── README.md               # Dokumentasi utama (file ini)
├── assets                  # Aset visual untuk ilustrasi konsep
│   ├── agent.png
│   ├── agent_langgraph.png
│   ├── router.png
│   └── router_langgraph.png
├── docs                    # Dokumentasi konsep LangGraph
│   ├── agent.md
│   ├── dynamic_breakpoint.md
│   ├── parallelization.md
│   ├── plan_and_execute.md
│   ├── router.md
│   ├── summarization.md
│   └── supervisor.md
├── graphy                  # Implementasi Python inti
│   ├── __init__.py
│   ├── agent.py
│   ├── dynamic_breakpoint.py
│   ├── parallelization.py
│   ├── plan_and_execute.py
│   ├── router.py
│   ├── summarization.py
│   └── supervisor.py
├── langgraph.json          # Konfigurasi contoh untuk LangGraph
├── poetry.lock             # File kunci dependensi untuk Poetry
└── pyproject.toml          # Konfigurasi proyek untuk Poetry
```

## Dokumentasi Penting

Repository ini mencakup beberapa file markdown di direktori `docs/`, masing-masing menjelaskan komponen atau fitur spesifik dari LangGraph:

- **[agent.md](docs/agent.md)**: Detail tentang desain dan fungsi agen dalam LangGraph.
- **[dynamic_breakpoint.md](docs/dynamic_breakpoint.md)**: Penjelasan tentang bagaimana breakpoint dinamis diterapkan dan digunakan.
- **[parallelization.md](docs/parallelization.md)**: Membahas metode dan praktik terbaik untuk paralelisasi tugas.
- **[plan_and_execute.md](docs/plan_and_execute.md)**: Proses perencanaan dan eksekusi tugas menggunakan LangGraph.
- **[router.md](docs/router.md)**: Gambaran mekanisme perutean tugas dalam sistem.
- **[summarization.md](docs/summarization.md)**: Penjelasan tentang ringkasan informasi untuk pemrosesan yang efisien.
- **[supervisor.md](docs/supervisor.md)**: Deskripsi sistem supervisi untuk memantau dan mengatur alur tugas.

## Cara Menjalankan

Untuk menjalankan repository ini, Anda memerlukan **LangGraph Studio**, sebuah antarmuka grafis untuk memvisualisasikan dan mengelola grafik LangGraph. 

### Langkah-langkah:

1. Unduh **LangGraph Studio** melalui tautan berikut: [Download LangGraph Studio](https://studio.langchain.com/).
2. Clone repository ini:
   ```bash
   git clone <repository-url>
   cd <repository-folder>
   ```
3. Instal dependensi menggunakan Poetry:
   ```bash
   poetry install
   ```
4. Buka **LangGraph Studio**, lalu impor path repository ini.
