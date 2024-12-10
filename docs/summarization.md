# Summarize Conversation

## Pendahuluan

Fungsi **summarize conversation** di LangGraph dirancang untuk menangani percakapan panjang yang melebihi batas tertentu. Fungsi ini penting dalam mengelola percakapan secara efisien karena:
- Menghindari akumulasi pesan yang tidak relevan.
- Memastikan konteks percakapan tetap terjaga dalam format yang ringkas.
- Mengoptimalkan performa model dengan menyediakan konteks yang lebih terfokus.

## Fungsi Summarize Conversation

### **Tujuan**

1. Membuat rangkuman dari percakapan yang telah berlangsung.
2. Memperbarui rangkuman ketika ada pesan baru.
3. Menghapus pesan lama untuk mengurangi beban memori.

### **Peran dalam LangGraph**

Dalam LangGraph, fungsi ini bertindak sebagai salah satu node dalam alur kerja (state graph). Node ini akan dieksekusi ketika percakapan mencapai kondisi tertentu, seperti jumlah pesan yang melebihi ambang batas.

## Alur Kerja

1. **Input**: Fungsi menerima status percakapan yang mencakup pesan saat ini dan rangkuman sebelumnya (jika ada).
2. **Proses**:
   - Membuat pesan yang meminta model untuk merangkum percakapan.
   - Jika rangkuman sudah ada, meminta model untuk memperbarui rangkuman dengan memperhitungkan pesan baru.
3. **Output**:
   - Rangkuman percakapan yang diperbarui.
   - Daftar pesan yang sudah dirangkum untuk dihapus.
4. **Hasil Akhir**: Status diperbarui dengan rangkuman baru dan hanya menyimpan beberapa pesan terakhir.

## Fitur Utama

1. **Dynamic Summarization**  
   Fungsi dapat menangani percakapan dengan panjang variabel. Jika percakapan menjadi terlalu panjang, rangkuman akan diperbarui untuk menjaga efisiensi.

2. **Message Pruning**  
   Setelah percakapan dirangkum, pesan-pesan lama yang tidak relevan akan dihapus untuk menghemat memori dan sumber daya.

3. **Konteks Berkesinambungan**  
   Rangkuman memperhatikan semua pesan sebelumnya untuk memastikan konteks percakapan tidak hilang.

## Kesimpulan

Fungsi summarize conversation adalah elemen penting dalam LangGraph untuk menangani percakapan panjang secara efisien. Dengan mekanisme rangkuman dan penghapusan pesan lama, fungsi ini memastikan bahwa alur percakapan tetap relevan, terfokus, dan dapat dikelola dengan baik.