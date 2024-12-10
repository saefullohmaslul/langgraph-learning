# Dynamic Breakpoint

## Pendahuluan

Dynamic breakpoint adalah mekanisme penting dalam LangGraph yang memungkinkan pengguna untuk menghentikan eksekusi alur kerja (workflow) secara dinamis berdasarkan kondisi tertentu. Dalam implementasi ini, dynamic breakpoint digunakan untuk memutuskan alur eksekusi ketika kondisi tertentu terpenuhi, misalnya panjang input melebihi batas yang ditentukan.

## Fungsi Dynamic Breakpoint

### Tujuan

1. Menghentikan alur kerja secara dinamis berdasarkan evaluasi kondisi runtime.
2. Memberikan fleksibilitas untuk menangani skenario yang tidak terduga dalam alur kerja.
3. Menyediakan mekanisme pengelolaan error atau interrupt dalam eksekusi workflow.

### Peran dalam LangGraph

Dynamic breakpoint diimplementasikan menggunakan pengecualian khusus, yaitu `NodeInterrupt`, yang memungkinkan node tertentu menghentikan eksekusi workflow saat kondisi tertentu terpenuhi. Hal ini menjadikan workflow lebih adaptif dan aman terhadap input yang tidak valid atau tidak diharapkan.

## Alur Kerja

1. **Input**: Workflow menerima status awal yang berisi data input.
2. **Proses**:
   - Setiap node dalam workflow memproses status.
   - Kondisi tertentu di dalam node dapat memicu breakpoint (contohnya: panjang input lebih dari 5 karakter).
3. **Output**:
   - Jika kondisi tercapai, `NodeInterrupt` di-raise, dan workflow dihentikan.
   - Jika tidak, workflow dilanjutkan ke node berikutnya.
4. **Hasil Akhir**: Workflow berhenti atau selesai dengan output yang diharapkan.

## Fitur Utama

1. **Interupsi Dinamis**
   Node dapat secara selektif menghentikan workflow berdasarkan kondisi runtime.

2. **Penanganan Error Kontekstual**  
   Ketika `NodeInterrupt` terjadi, pengguna dapat menangkap dan menangani interupsi dengan memberikan pesan atau aksi korektif.

3. **Alur Eksekusi Fleksibel**  
   Workflow dapat menyesuaikan eksekusi berdasarkan input tanpa memengaruhi node lainnya.

## Implementasi Dynamic Breakpoint

### 1. Pengecekan Kondisi

Node kedua (`step_2`) memeriksa panjang input dan memutuskan apakah workflow harus dihentikan. Jika panjang input lebih dari 5 karakter, `NodeInterrupt` di-raise.

```python
def step_2(state: State) -> State:
    if len(state["input"]) > 5:
        raise NodeInterrupt(f"Received input that is longer than 5 characters: {state['input']}")

    print("---Step 2---")
    return state
```

### 2. Mekanisme Edge

Workflow diatur dalam urutan berikut:
- `START` → `step_1` → `step_2` → `step_3` → `END`.

Namun, jika interupsi terjadi di `step_2`, workflow langsung dihentikan tanpa melanjutkan ke `step_3`.

### 3. Penanganan Workflow

Dynamic breakpoint memungkinkan penghentian eksekusi dengan pesan khusus, sehingga mempermudah debugging atau tindakan selanjutnya.

## Keunggulan Dynamic Breakpoint

1. **Validasi Input**
   Memastikan bahwa input yang tidak valid dapat dihentikan sebelum melanjutkan eksekusi, mencegah kesalahan lebih lanjut.

2. **Debugging yang Mudah**
   Dengan pesan interupsi, pengguna dapat langsung mengetahui penyebab penghentian alur.

3. **Fleksibilitas Kondisional**
   Node dapat dikonfigurasi untuk memeriksa berbagai kondisi yang spesifik sesuai kebutuhan workflow.

## Contoh Penggunaan

### Input Valid
```python
state = {"input": "short"}
graph.run(state)
```
**Output**:
```
---Step 1---
---Step 2---
---Step 3---
```

### Input Tidak Valid
```python
state = {"input": "this_is_long"}
graph.run(state)
```
**Output**:
```
NodeInterrupt: Received input that is longer than 5 characters: this_is_long
```

---

## Kesimpulan

Dynamic breakpoint di LangGraph adalah mekanisme untuk menangani interupsi runtime dalam workflow. Dengan menggunakan `NodeInterrupt`, pengguna dapat mengelola kondisi error secara dinamis dan menjaga alur kerja tetap efisien dan aman.