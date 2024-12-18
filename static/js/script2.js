// Memuat daftar pegawai untuk dropdown
function loadEmployeeDropdown() {
    fetch('http://localhost:8000/api/get-data-pegawai') // Ganti dengan API yang mengembalikan daftar pegawai
        .then(response => {
            if (!response.ok) {
                throw new Error('Gagal memuat data pegawai.');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                const employeeSelect = document.getElementById('employee-select');
                data.employees.forEach(employee => {
                    const option = document.createElement('option');
                    option.value = employee.id;
                    option.textContent = employee.name;
                    employeeSelect.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('Error loading employee dropdown:', error);
        });
}

// Fungsi untuk mengambil data grafik per pegawai
function fetchEmployeeChart(employeeId, startDate, endDate) {
    fetch(`http://localhost:8000/api/log-absen/chart/employee?employee_id=${employeeId}&start_date=${startDate}&end_date=${endDate}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Gagal memuat data grafik per pegawai.');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                renderEmployeeChart(data.chartData);
            } else {
                alert('Tidak ada data absensi untuk pegawai ini.');
            }
        })
        .catch(error => {
            console.error('Error fetching employee chart data:', error);
        });
}

// Render grafik per pegawai
function renderEmployeeChart(chartData) {
    const ctx = document.getElementById('employeeChart').getContext('2d');
    document.getElementById('employeeChart').style.display = 'block'; // Tampilkan grafik pegawai

    // Hapus instance grafik sebelumnya
    if (window.employeeChartInstance) {
        window.employeeChartInstance.destroy();
    }

    window.employeeChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.labels,
            datasets: [
                {
                    label: 'Kehadiran',
                    data: chartData.presentData,
                    borderColor: '#1abc9c',
                    fill: false,
                },
                {
                    label: 'Tidak Hadir',
                    data: chartData.absentData,
                    borderColor: '#e74c3c',
                    fill: false,
                },
            ],
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label: (context) => `${context.dataset.label}: ${context.raw}`,
                    },
                },
            },
        },
    });
}

// Event listener untuk tombol filter grafik pegawai
document.getElementById('filter-employee-chart-btn').addEventListener('click', function() {
    const employeeId = document.getElementById('employee-select').value;
    const dateRange = document.getElementById('date-range').value;

    if (!employeeId) {
        alert('Silakan pilih pegawai.');
        return;
    }

    const [startDate, endDate] = dateRange.split(' to '); // Rentang tanggal dalam format "Y-m-d to Y-m-d"
    fetchEmployeeChart(employeeId, startDate, endDate);
});

document.addEventListener('DOMContentLoaded', function () {
    flatpickr("#date-range", {
        mode: "range", // untuk rentang tanggal
        dateFormat: "Y-m-d",
    });
});

// Panggil fungsi untuk memuat dropdown saat halaman dimuat
window.addEventListener('DOMContentLoaded', function () {
    loadEmployeeDropdown();
});

document.getElementById('add-employee-form').addEventListener('submit', function(event) {
    event.preventDefault(); // Menghentikan form agar tidak reload halaman

    // Menyiapkan data untuk dikirim
    const formData = new FormData();
    formData.append('employee-name', document.getElementById('employee-name').value);
    formData.append('employee-nip', document.getElementById('employee-nip').value);
    formData.append('employee-phone', document.getElementById('employee-phone').value);
    formData.append('employee-address', document.getElementById('employee-address').value);

    // Mengirim data ke backend menggunakan AJAX
    fetch('http://localhost:8000/api/add_data_pegawai', {
        method: 'POST',
        body: formData,
        headers: {
            'Accept': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        // Menampilkan pesan sukses atau error
        if (data.success) {
            document.getElementById('result-message').innerHTML = `
                <p style="color: green;">Pegawai berhasil ditambahkan: ${data.employee.name}</p>
            `;
        } else {
            document.getElementById('result-message').innerHTML = `
                <p style="color: red;">Gagal menambahkan pegawai.</p>
            `;
        }
    })
    .catch(error => {
        document.getElementById('result-message').innerHTML = `
            <p style="color: red;">Terjadi kesalahan: ${error.message}</p>
        `;
    });
});

