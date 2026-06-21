let html5QrCode;
let currentStudentData = null;
let isScanning = false;
let allStudents = [];  // cache for search filtering

// ─────────────────────────────────────────────
// iOS FIX: Patch Html5Qrcode to inject
// playsinline BEFORE the video element plays.
// ─────────────────────────────────────────────
function patchHtml5QrcodeForIOS() {
    if (!window.Html5Qrcode) return;

    const origStart = Html5Qrcode.prototype.start;
    Html5Qrcode.prototype.start = function (...args) {
        const result = origStart.apply(this, args);
        result.then(() => {
            const container = document.getElementById(this._elementId || 'reader');
            if (!container) return;
            const video = container.querySelector('video');
            if (video) {
                video.setAttribute('playsinline', '');
                video.setAttribute('webkit-playsinline', '');
                video.muted = true;
                video.play().catch(() => {});
            }
        }).catch(() => {});
        return result;
    };
}

// ─────────────────────────────────────────────
// Helper: is the QR scan tab currently active?
// ─────────────────────────────────────────────
function isScanTabActive() {
    return document.getElementById('scan-panel').classList.contains('active');
}

// ─────────────────────────────────────────────
// QR Scanner button setup
// ─────────────────────────────────────────────
function setupScannerButton() {
    const btn = document.getElementById('start-scan-btn');
    if (!btn) {
        console.error('Start scan button not found!');
        return;
    }

    patchHtml5QrcodeForIOS();

    // ✅ iOS FIX: getUserMedia must be called DIRECTLY inside the
    // click handler — no async/await, no intermediate function call.
    btn.addEventListener('click', function (event) {
        event.preventDefault();
        event.stopPropagation();

        if (isScanning) return;

        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Requesting camera...';

        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-camera"></i> ចាប់ផ្ដើមស្កេន';
            alert(
                'Your browser does not support camera access.\n\n' +
                'Please use:\n- Safari (iOS)\n- Chrome\n- Firefox\n- Edge'
            );
            return;
        }

        navigator.mediaDevices
            .getUserMedia({
                video: {
                    facingMode: { ideal: 'environment' },
                    width:  { min: 320, ideal: 480, max: 720 },
                    height: { min: 320, ideal: 480, max: 720 },
                },
                audio: false,
            })
            .then(stream => {
                stream.getTracks().forEach(track => track.stop());
                startScanner();
            })
            .catch(err => {
                btn.disabled = false;
                btn.innerHTML = '<i class="bi bi-camera"></i> ចាប់ផ្ដើមស្កេន';

                if (err.name === 'OverconstrainedError' || err.name === 'ConstraintError') {
                    navigator.mediaDevices
                        .getUserMedia({ video: true, audio: false })
                        .then(stream => {
                            stream.getTracks().forEach(track => track.stop());
                            startScanner();
                        })
                        .catch(fallbackErr => {
                            btn.disabled = false;
                            btn.innerHTML = '<i class="bi bi-camera"></i> ចាប់ផ្ដើមស្កេន';
                            handleCameraError(fallbackErr);
                        });
                } else {
                    handleCameraError(err);
                }
            });
    });
}

// ─────────────────────────────────────────────
// Camera error messages
// ─────────────────────────────────────────────
function handleCameraError(err) {
    console.error('Camera error:', err.name, err.message);

    if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        alert(
            '❌ Camera permission denied.\n\n' +
            '📱 On iPhone/iPad (Safari):\n' +
            '1. Go to Settings → Safari → Camera\n' +
            '   Set to "Allow"\n' +
            '   — OR —\n' +
            '   Settings → [This Website] → Camera → Allow\n' +
            '2. Reload the page and try again\n\n' +
            '💻 On Desktop:\n' +
            '1. Click the camera icon in the address bar\n' +
            '2. Select "Allow"\n' +
            '3. Try again'
        );
    } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        alert('❌ No camera found on this device.\n\nMake sure your device has a camera and try again.');
    } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
        alert('❌ Camera is already in use by another app.\n\nClose other apps using the camera and try again.');
    } else if (err.name === 'SecurityError') {
        alert(
            '❌ Camera access blocked for security reasons.\n\n' +
            '⚠️ Browsers require HTTPS for camera access.\n\n' +
            'Make sure the site URL starts with https://'
        );
    } else {
        alert(
            '❌ Camera error: ' + err.name + '\n\n' +
            'Please ensure:\n' +
            '1. Camera permission is granted\n' +
            '2. Device has a camera\n' +
            '3. No other app is using it'
        );
    }
}

// ─────────────────────────────────────────────
// QR Scanner
// ─────────────────────────────────────────────
function startScanner() {
    if (isScanning) return;

    const btn = document.getElementById('start-scan-btn');
    html5QrCode = new Html5Qrcode('reader');

    const config = {
        fps: 10,
        qrbox: { width: 250, height: 250 },
        aspectRatio: 1.0,
        videoConstraints: { facingMode: { ideal: 'environment' } },
    };

    const cameraConfigs = [
        { facingMode: { ideal: 'environment' } },
        { facingMode: { ideal: 'user' } },
    ];

    const attemptCameraStart = (configIndex = 0) => {
        if (configIndex >= cameraConfigs.length) {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-camera"></i> ចាប់ផ្ដើមស្កេន';
            alert(
                'Cannot access camera. Please check:\n\n' +
                '1. Camera permission is granted\n' +
                '2. Device has a camera\n' +
                '3. No other app is using the camera'
            );
            return;
        }

        const cameraLabel = configIndex === 0 ? 'back' : 'front';

        html5QrCode
            .start(cameraConfigs[configIndex], config, onScanSuccess, onScanError)
            .then(() => {
                isScanning = true;
                btn.innerHTML = '<i class="bi bi-camera-video-fill"></i> ម៉ាស៊ីនស្កេនកំពុងដំណើរការ...';
                btn.classList.replace('btn-primary', 'btn-success');
                btn.disabled = true;
                console.log(`Scanner started using ${cameraLabel} camera`);
                ensureVideoPlaysinline();
            })
            .catch(err => {
                console.warn(`Failed to start with ${cameraLabel} camera:`, err.name);
                attemptCameraStart(configIndex + 1);
            });
    };

    attemptCameraStart();
}

function ensureVideoPlaysinline() {
    const reader = document.getElementById('reader');
    if (!reader) return;

    const setAttrs = (video) => {
        if (!video.hasAttribute('playsinline')) {
            video.setAttribute('playsinline', '');
            video.setAttribute('webkit-playsinline', '');
            video.muted = true;
            video.play().catch(() => {});
        }
    };

    const existing = reader.querySelector('video');
    if (existing) { setAttrs(existing); return; }

    const observer = new MutationObserver(() => {
        const video = reader.querySelector('video');
        if (video) {
            observer.disconnect();
            setAttrs(video);
        }
    });
    observer.observe(reader, { childList: true, subtree: true });
}

function stopScanner() {
    if (html5QrCode && isScanning) {
        html5QrCode.stop()
            .then(() => {
                isScanning = false;
                const btn = document.getElementById('start-scan-btn');
                btn.innerHTML = '<i class="bi bi-camera"></i> ចាប់ផ្ដើមស្កេន';
                btn.classList.replace('btn-success', 'btn-primary');
                btn.disabled = false;
            })
            .catch(err => console.error('មិនអាចបញ្ឈប់ការស្កេន:', err));
    }
}

// ─────────────────────────────────────────────
// Scan callbacks
// ─────────────────────────────────────────────
function onScanSuccess(decodedText) {
    stopScanner();
    playBeep();
    fetchStudentInfo(decodedText.trim());
}

function onScanError(err) {
    console.debug('Scan error:', err);
}

// ─────────────────────────────────────────────
// Audio beep
// ─────────────────────────────────────────────
function playBeep() {
    try {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioCtx.createOscillator();
        const gainNode = audioCtx.createGain();
        oscillator.connect(gainNode);
        gainNode.connect(audioCtx.destination);
        oscillator.type = 'sine';
        oscillator.frequency.setValueAtTime(800, audioCtx.currentTime);
        gainNode.gain.setValueAtTime(0.3, audioCtx.currentTime);
        oscillator.start(audioCtx.currentTime);
        oscillator.stop(audioCtx.currentTime + 0.2);
    } catch (e) { /* silent fail */ }
}

// ─────────────────────────────────────────────
// Searchable Student Dropdown
// ─────────────────────────────────────────────
function setupStudentDropdown() {
    const searchInput  = document.getElementById('student-search');
    const resultsList  = document.getElementById('student-results');
    const hiddenInput  = document.getElementById('selected-student-id');
    const selectedName = document.getElementById('selected-student-name');
    const proceedBtn   = document.getElementById('select-student-btn');

    if (!searchInput || !resultsList || !hiddenInput || !proceedBtn) return;

    // Filter and render results as user types
    searchInput.addEventListener('input', function () {
        const query = this.value.trim().toLowerCase();

        // Clear selection when user edits the search
        hiddenInput.value = '';
        selectedName.textContent = '';
        proceedBtn.disabled = true;

        if (!query) {
            resultsList.innerHTML = '';
            resultsList.classList.add('d-none');
            return;
        }

        const matches = allStudents.filter(s =>
            s.name.toLowerCase().includes(query) ||
            s.id.toLowerCase().includes(query)
        );

        renderResults(matches);
    });

    // Hide results when clicking outside
    document.addEventListener('click', function (e) {
        if (!e.target.closest('#student-search-wrapper')) {
            resultsList.classList.add('d-none');
        }
    });

    // Proceed button
    proceedBtn.addEventListener('click', function () {
        const studentId = hiddenInput.value;
        if (!studentId) {
            alert('សូមជ្រើសរើសសិស្ស។');
            return;
        }
        fetchStudentInfo(studentId);
    });
}

function renderResults(matches) {
    const resultsList  = document.getElementById('student-results');
    const hiddenInput  = document.getElementById('selected-student-id');
    const searchInput  = document.getElementById('student-search');
    const selectedName = document.getElementById('selected-student-name');
    const proceedBtn   = document.getElementById('select-student-btn');

    resultsList.innerHTML = '';

    if (matches.length === 0) {
        resultsList.innerHTML = '<li class="list-group-item text-muted">No students found</li>';
        resultsList.classList.remove('d-none');
        return;
    }

    matches.slice(0, 20).forEach(student => {  // cap at 20 for performance
        const li = document.createElement('li');
        li.className = 'list-group-item list-group-item-action';
        li.style.cursor = 'pointer';

        // Highlight matched portion
        const query = searchInput.value.trim();
        li.innerHTML = `
            <span class="fw-semibold">${highlight(student.name, query)}</span>
            <small class="text-muted ms-2">${highlight(student.id, query)}</small>
        `;

        li.addEventListener('click', function () {
            hiddenInput.value  = student.id;
            searchInput.value  = `${student.name} (${student.id})`;
            selectedName.textContent = '';
            proceedBtn.disabled = false;
            resultsList.classList.add('d-none');
        });

        resultsList.appendChild(li);
    });

    resultsList.classList.remove('d-none');
}

// Wrap matching text in <mark> for highlighting
function highlight(text, query) {
    if (!query) return text;
    const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    return text.replace(new RegExp(`(${escaped})`, 'gi'), '<mark class="p-0">$1</mark>');
}

function loadStudentList() {
    fetch('/api/students', {
        headers: { 'X-CSRFToken': getCSRFToken() },
    })
        .then(res => res.json())
        .then(data => {
            if (data.students && Array.isArray(data.students)) {
                allStudents = data.students;
            }
        })
        .catch(err => console.error('Failed to load student list:', err));
}

// ─────────────────────────────────────────────
// Student / Payment API
// ─────────────────────────────────────────────
function fetchStudentInfo(studentId) {
    const resultDiv = document.getElementById('scan-result');
    if (resultDiv) resultDiv.innerHTML = '<div class="alert alert-info">Loading student information...</div>';

    fetch(`/api/student/${studentId}`, {
        headers: { 'X-CSRFToken': getCSRFToken() },
    })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                showError(data.error);
                return;
            }
            currentStudentData = data.student;
            
            // Check if student has a record for today
            checkTodayRecord(studentId);
            
            if (resultDiv) resultDiv.innerHTML = '';
        })
        .catch(err => {
            console.error('Error fetching student:', err);
            showError('Failed to fetch student information. Please try again.');
        });
}

// ─────────────────────────────────────────────
// Check if student has a record for today
// ─────────────────────────────────────────────
function checkTodayRecord(studentId) {
    fetch(`/api/today-record/${studentId}`, {
        headers: { 'X-CSRFToken': getCSRFToken() },
    })
        .then(res => res.json())
        .then(data => {
            if (data.has_record) {
                showTodayRecordModal(data.record, currentStudentData);
            } else {
                showConfirmationModal(currentStudentData);
            }
        })
        .catch(err => {
            console.error('Error checking today\'s record:', err);
            // If check fails, just show the confirmation modal
            showConfirmationModal(currentStudentData);
        });
}

function showConfirmationModal(student) {
    document.getElementById('student-name').textContent = student.name;
    document.getElementById('student-id').textContent = student.id;
    
    let infoText = '';
    if (student.gender) {
        infoText += student.gender;
    }
    if (student.grade_level) {
        if (infoText) infoText += ' • ';
        infoText += student.grade_level;
    }
    document.getElementById('student-info').textContent = infoText;

    const container = document.getElementById('courses-checkboxes');
    container.innerHTML = '';
    container.style.display = 'grid';
    container.style.gridTemplateColumns = 'repeat(auto-fit, minmax(150px, 1fr))';
    container.style.gap = '12px';

    student.courses.forEach(course => {
        const div = document.createElement('div');
        div.className = 'course-card';
        div.style.cssText = `
            padding: 12px;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            cursor: pointer;
            text-align: center;
            transition: all 0.2s ease;
            background: white;
        `;
        
        const isDefault = course.is_default;
        if (isDefault) {
            div.style.borderColor = '#0d6efd';
            div.style.backgroundColor = '#e7f1ff';
        }

        const badgeHtml = isDefault ? '<span class="badge bg-info mt-2">Default</span>' : '';
        div.innerHTML = `
            <input class="form-check-input course-check"
                   type="checkbox"
                   value="${course.id}"
                   data-fee="${course.fee}"
                   id="course-${course.id}"
                   style="display:none;"
                   ${isDefault ? 'checked' : ''}>
            <h6 class="mb-2" style="font-weight:600;">${course.name}</h6>
            <p class="mb-0" style="font-size:18px;font-weight:bold;color:#0d6efd;">៛${course.fee.toFixed(0)}</p>
            <small style="color:#6c757d;">/day</small>
            ${badgeHtml}
        `;

        div.addEventListener('click', function(e) {
            if (e.target.tagName !== 'INPUT') {
                const checkbox = this.querySelector('.course-check');
                checkbox.checked = !checkbox.checked;
                checkbox.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });

        // Highlight on hover/selection
        div.addEventListener('change', function(e) {
            const checkbox = this.querySelector('.course-check');
            if (checkbox && checkbox.checked) {
                this.style.borderColor = '#198754';
                this.style.backgroundColor = '#f0fdf4';
                this.style.boxShadow = '0 0 0 3px rgba(25, 135, 84, 0.1)';
            } else {
                this.style.borderColor = '#dee2e6';
                this.style.backgroundColor = 'white';
                this.style.boxShadow = 'none';
            }
        }, true);

        container.appendChild(div);
    });

    document.querySelectorAll('.course-check').forEach(cb => {
        cb.addEventListener('change', function() {
            const card = this.closest('.course-card');
            if (this.checked) {
                card.style.borderColor = '#198754';
                card.style.backgroundColor = '#f0fdf4';
                card.style.boxShadow = '0 0 0 3px rgba(25, 135, 84, 0.1)';
            } else {
                card.style.borderColor = '#dee2e6';
                card.style.backgroundColor = 'white';
                card.style.boxShadow = 'none';
            }
            updateTotal();
        });
    });

    document.getElementById('tabs-check').checked = false;
    document.getElementById('payment-status').style.display = 'none';
    document.getElementById('confirm-btn').style.display = 'inline-block';

    updateTotal();

    const modal = new bootstrap.Modal(document.getElementById('confirmModal'));
    modal.show();
}

function updateTotal() {
    let total = 0;
    document.querySelectorAll('.course-check:checked').forEach(cb => {
        total += parseFloat(cb.dataset.fee);
    });
    document.getElementById('total-display').textContent = total.toFixed(0);
}

// ─────────────────────────────────────────────
// Show today's record for modification
// ─────────────────────────────────────────────
function showTodayRecordModal(record, student) {
    document.getElementById('today-record-student-name').textContent = student.name;
    document.getElementById('today-record-date').textContent = new Date(record.date).toLocaleDateString();
    
    // Show previously recorded courses
    const coursesList = record.courses.map(c => c.name).join(', ');
    document.getElementById('today-record-courses').textContent = coursesList || 'None';

    // Show new course options to select
    const newCoursesContainer = document.getElementById('today-record-new-courses');
    newCoursesContainer.innerHTML = '';
    newCoursesContainer.style.display = 'grid';
    newCoursesContainer.style.gridTemplateColumns = 'repeat(auto-fit, minmax(150px, 1fr))';
    newCoursesContainer.style.gap = '12px';

    let recordCourseIds = record.courses.map(c => c.id);

    student.courses.forEach(course => {
        const div = document.createElement('div');
        div.className = 'course-card';
        const isChecked = recordCourseIds.includes(course.id);
        
        div.style.cssText = `
            padding: 12px;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            cursor: pointer;
            text-align: center;
            transition: all 0.2s ease;
            background: white;
        `;

        if (isChecked) {
            div.style.borderColor = '#198754';
            div.style.backgroundColor = '#f0fdf4';
        }

        const badgeHtml = isChecked ? '<span class="badge bg-success mt-2">Previous</span>' : '';
        div.innerHTML = `
            <input class="form-check-input today-record-course-check"
                   type="checkbox"
                   value="${course.id}"
                   data-fee="${course.fee}"
                   id="today-record-course-${course.id}"
                   style="display:none;"
                   ${isChecked ? 'checked' : ''}>
            <h6 class="mb-2" style="font-weight:600;">${course.name}</h6>
            <p class="mb-0" style="font-size:18px;font-weight:bold;color:#0d6efd;">៛${course.fee.toFixed(0)}</p>
            <small style="color:#6c757d;">/day</small>
            ${badgeHtml}
        `;

        div.addEventListener('click', function(e) {
            if (e.target.tagName !== 'INPUT') {
                const checkbox = this.querySelector('.today-record-course-check');
                checkbox.checked = !checkbox.checked;
                checkbox.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });

        newCoursesContainer.appendChild(div);
    });

    document.querySelectorAll('.today-record-course-check').forEach(cb => {
        cb.addEventListener('change', function() {
            const card = this.closest('.course-card');
            if (this.checked) {
                card.style.borderColor = '#198754';
                card.style.backgroundColor = '#f0fdf4';
                card.style.boxShadow = '0 0 0 3px rgba(25, 135, 84, 0.1)';
            } else {
                card.style.borderColor = '#dee2e6';
                card.style.backgroundColor = 'white';
                card.style.boxShadow = 'none';
            }
            updateTodayRecordTotal();
        });
    });

    document.getElementById('today-record-tabs-check').checked = !record.is_paid;
    document.getElementById('today-record-status').style.display = 'none';
    document.getElementById('today-record-update-btn').style.display = 'inline-block';

    // Store the current record ID for updating
    document.getElementById('todayRecordModal').dataset.recordId = record.id;

    updateTodayRecordTotal();

    const modal = new bootstrap.Modal(document.getElementById('todayRecordModal'));
    modal.show();
}

function updateTodayRecordTotal() {
    let total = 0;
    document.querySelectorAll('.today-record-course-check:checked').forEach(cb => {
        total += parseFloat(cb.dataset.fee);
    });
    document.getElementById('today-record-total-display').textContent = total.toFixed(0);
}

// ─────────────────────────────────────────────
// Payment confirmation
// ─────────────────────────────────────────────
document.getElementById('confirm-btn').addEventListener('click', function () {
    const selectedCourses = [];
    document.querySelectorAll('.course-check:checked').forEach(cb => {
        selectedCourses.push(parseInt(cb.value));
    });

    if (selectedCourses.length === 0) {
        alert('សូមជ្រើសរើសយ៉ាងតិច១វគ្គសិក្សា។');
        return;
    }

    const tabs = document.getElementById('tabs-check').checked;
    document.getElementById('payment-status').style.display = 'block';
    this.style.display = 'none';

    fetch('/api/record_payment', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),
        },
        body: JSON.stringify({
            student_id: currentStudentData.id,
            course_ids: selectedCourses,
            tabs: tabs,
        }),
    })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const modal = bootstrap.Modal.getInstance(document.getElementById('confirmModal'));
                modal.hide();

                const status = data.is_paid ? 'Paid' : 'Tabs';
                showToast(`Payment recorded! ${currentStudentData.name} - ៛${data.total.toFixed(0)} (${status})`);

                setTimeout(() => {
                    const resultDiv = document.getElementById('scan-result');
                    if (resultDiv) {
                        resultDiv.innerHTML =
                            `<div class="alert alert-success">Last: ${currentStudentData.name} - $${data.total.toFixed(0)} (${status})</div>`;
                    }
                    if (isScanTabActive()) {
                        startScanner();
                        const btn = document.getElementById('start-scan-btn');
                        btn.innerHTML = '<i class="bi bi-camera-video-fill"></i> ម៉ាស៊ីនស្កេនកំពុងដំណើរការ...';
                        btn.classList.replace('btn-primary', 'btn-success');
                    }
                }, 1500);
            } else {
                alert('Error: ' + (data.error || 'Unknown error'));
                document.getElementById('payment-status').style.display = 'none';
                document.getElementById('confirm-btn').style.display = 'inline-block';
            }
        })
        .catch(err => {
            console.error('Error recording payment:', err);
            alert('ការបង់ប្រាក់មិនបានជោគជ័យ។ សូមព្យាយាមម្តងទៀត។');
            document.getElementById('payment-status').style.display = 'none';
            document.getElementById('confirm-btn').style.display = 'inline-block';
        });
});

// ─────────────────────────────────────────────
// Update today's record
// ─────────────────────────────────────────────
document.getElementById('today-record-update-btn').addEventListener('click', function () {
    const selectedCourses = [];
    document.querySelectorAll('.today-record-course-check:checked').forEach(cb => {
        selectedCourses.push(parseInt(cb.value));
    });

    if (selectedCourses.length === 0) {
        alert('សូមជ្រើសរើសយ៉ាងតិច១វគ្គសិក្សា។');
        return;
    }

    const tabs = document.getElementById('today-record-tabs-check').checked;
    const recordId = document.getElementById('todayRecordModal').dataset.recordId;
    
    document.getElementById('today-record-status').style.display = 'block';
    this.style.display = 'none';

    fetch(`/api/update_payment/${recordId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),
        },
        body: JSON.stringify({
            course_ids: selectedCourses,
            tabs: tabs,
        }),
    })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const modal = bootstrap.Modal.getInstance(document.getElementById('todayRecordModal'));
                modal.hide();

                const status = data.is_paid ? 'Paid' : 'Tabs';
                showToast(`ក៍ត្របង់ប្រាក់បានកែប្រែ! ${currentStudentData.name} - ៛${data.total.toFixed(0)} (${status})`);

                setTimeout(() => {
                    const resultDiv = document.getElementById('scan-result');
                    if (resultDiv) {
                        resultDiv.innerHTML =
                            `<div class="alert alert-success">Last: ${currentStudentData.name} - ៛${data.total.toFixed(0)} (${status})</div>`;
                    }
                    if (isScanTabActive()) {
                        startScanner();
                        const btn = document.getElementById('start-scan-btn');
                        btn.innerHTML = '<i class="bi bi-camera-video-fill"></i> Scanner Running...';
                        btn.classList.replace('btn-primary', 'btn-success');
                    }
                }, 1500);
            } else {
                alert('Error: ' + (data.error || 'Unknown error'));
                document.getElementById('today-record-status').style.display = 'none';
                document.getElementById('today-record-update-btn').style.display = 'inline-block';
            }
        })
        .catch(err => {
            console.error('Error updating payment:', err);
            alert('ការបង់ប្រាក់មិនបានជោគជ័យ។ សូមព្យាយាមម្តងទៀត។');
            document.getElementById('today-record-status').style.display = 'none';
            document.getElementById('today-record-update-btn').style.display = 'inline-block';
        });
});

// ─────────────────────────────────────────────
// Modal events
// ─────────────────────────────────────────────
document.getElementById('confirmModal').addEventListener('hidden.bs.modal', function () {
    if (
        document.getElementById('payment-status').style.display === 'none' &&
        isScanTabActive()
    ) {
        startScanner();
        const btn = document.getElementById('start-scan-btn');
        btn.innerHTML = '<i class="bi bi-camera-video-fill"></i> Scanner Running...';
        btn.classList.replace('btn-primary', 'btn-success');
    }

    // Reset the student search panel after modal closes
    const searchInput  = document.getElementById('student-search');
    const hiddenInput  = document.getElementById('selected-student-id');
    const proceedBtn   = document.getElementById('select-student-btn');
    const resultsList  = document.getElementById('student-results');
    if (searchInput)  searchInput.value = '';
    if (hiddenInput)  hiddenInput.value = '';
    if (proceedBtn)   proceedBtn.disabled = true;
    if (resultsList)  resultsList.classList.add('d-none');
});

// ─────────────────────────────────────────────
// Modal events
// ─────────────────────────────────────────────
document.getElementById('confirmModal').addEventListener('hidden.bs.modal', function () {
    if (
        document.getElementById('payment-status').style.display === 'none' &&
        isScanTabActive()
    ) {
        startScanner();
        const btn = document.getElementById('start-scan-btn');
        btn.innerHTML = '<i class="bi bi-camera-video-fill"></i> Scanner Running...';
        btn.classList.replace('btn-primary', 'btn-success');
    }

    // Reset the student search panel after modal closes
    const searchInput  = document.getElementById('student-search');
    const hiddenInput  = document.getElementById('selected-student-id');
    const proceedBtn   = document.getElementById('select-student-btn');
    const resultsList  = document.getElementById('student-results');
    if (searchInput)  searchInput.value = '';
    if (hiddenInput)  hiddenInput.value = '';
    if (proceedBtn)   proceedBtn.disabled = true;
    if (resultsList)  resultsList.classList.add('d-none');
});

document.getElementById('select-tab').addEventListener('shown.bs.tab', function () {
    stopScanner();
});

// Today's record modal close handler
document.getElementById('todayRecordModal').addEventListener('hidden.bs.modal', function () {
    if (
        document.getElementById('today-record-status').style.display === 'none' &&
        isScanTabActive()
    ) {
        startScanner();
        const btn = document.getElementById('start-scan-btn');
        btn.innerHTML = '<i class="bi bi-camera-video-fill"></i> Scanner Running...';
        btn.classList.replace('btn-primary', 'btn-success');
    }

    // Reset the student search panel after modal closes
    const searchInput  = document.getElementById('student-search');
    const hiddenInput  = document.getElementById('selected-student-id');
    const proceedBtn   = document.getElementById('select-student-btn');
    const resultsList  = document.getElementById('student-results');
    if (searchInput)  searchInput.value = '';
    if (hiddenInput)  hiddenInput.value = '';
    if (proceedBtn)   proceedBtn.disabled = true;
    if (resultsList)  resultsList.classList.add('d-none');
});

// ─────────────────────────────────────────────
// Shared helpers
// ─────────────────────────────────────────────
function showError(message) {
    const resultDiv = document.getElementById('scan-result');
    if (resultDiv) {
        resultDiv.innerHTML = `<div class="alert alert-danger">${message}</div>`;
    }
    if (isScanTabActive()) {
        startScanner();
        const btn = document.getElementById('start-scan-btn');
        btn.innerHTML = '<i class="bi bi-camera-video-fill"></i> Scanner Running...';
        btn.classList.replace('btn-primary', 'btn-success');
    }
}

function showToast(message) {
    document.getElementById('toast-message').textContent = message;
    const toast = new bootstrap.Toast(document.getElementById('successToast'));
    toast.show();
}

function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

// ─────────────────────────────────────────────
// Init
// ─────────────────────────────────────────────
function setupPage() {
    setupScannerButton();
    setupStudentDropdown();
    loadStudentList();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupPage);
} else {
    setupPage();
}

console.log('Scan.js loaded and initialized');