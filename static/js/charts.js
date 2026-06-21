// Chart.js utility functions for monthly reports

// Color palette
const colors = {
    blue: 'rgba(54, 162, 235, 0.7)',
    blueBorder: 'rgba(54, 162, 235, 1)',
    green: 'rgba(75, 192, 192, 0.7)',
    greenBorder: 'rgba(75, 192, 192, 1)',
    red: 'rgba(255, 99, 132, 0.7)',
    redBorder: 'rgba(255, 99, 132, 1)',
    orange: 'rgba(255, 159, 64, 0.7)',
    purple: 'rgba(153, 102, 255, 0.7)',
    yellow: 'rgba(255, 205, 86, 0.7)'
};

// Create line chart for daily revenue
function createRevenueChart(ctx, labels, data) {
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Daily Revenue ($)',
                data: data,
                borderColor: colors.blueBorder,
                backgroundColor: colors.blue,
                tension: 0.3,
                fill: true,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Daily Revenue'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Revenue ($)'
                    }
                }
            }
        }
    });
}

// Create attendance chart (present vs absent)
function createAttendanceChart(ctx, labels, presentData, absentData) {
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Present',
                    data: presentData,
                    borderColor: colors.greenBorder,
                    backgroundColor: colors.green,
                    tension: 0.3,
                    fill: true,
                    pointRadius: 4
                },
                {
                    label: 'Absent',
                    data: absentData,
                    borderColor: colors.redBorder,
                    backgroundColor: colors.red,
                    tension: 0.3,
                    fill: true,
                    pointRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Daily Attendance'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Students'
                    }
                }
            }
        }
    });
}

// Create bar chart for revenue by course
function createCourseChart(ctx, labels, data) {
    const backgroundColors = [
        colors.blue, colors.green, colors.red, 
        colors.orange, colors.purple, colors.yellow
    ];
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Revenue by Course ($)',
                data: data,
                backgroundColor: backgroundColors.slice(0, data.length),
                borderColor: backgroundColors.slice(0, data.length).map(c => c.replace('0.7', '1')),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Revenue by Course'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Revenue ($)'
                    }
                }
            }
        }
    });
}

// Create pie chart for paid vs tabs
function createPaidPieChart(ctx, paid, tabs) {
    return new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['Paid', 'Tabs (Pay Later)'],
            datasets: [{
                data: [paid, tabs],
                backgroundColor: [colors.green, colors.orange],
                borderColor: [colors.greenBorder, colors.redBorder],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Paid vs Tabs Revenue'
                },
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// Export functions for use in templates
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        createRevenueChart,
        createAttendanceChart,
        createCourseChart,
        createPaidPieChart
    };
}