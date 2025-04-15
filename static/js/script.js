document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.querySelector('form[action="/search"]');
    const searchInput = document.querySelector('input[name="query"]');
    const mainElement = document.querySelector('main');
    
    // Create a results container that will be populated after search
    const resultsContainer = document.createElement('section');
    resultsContainer.className = 'results-section';
    mainElement.appendChild(resultsContainer);
    
    searchForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const searchQuery = searchInput.value.trim();
        if (!searchQuery) return;
        
        // Show loading state
        resultsContainer.innerHTML = '<div class="loading">Searching courses...</div>';
        
        try {
            const response = await fetch('/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `name=${encodeURIComponent(searchQuery)}`
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                resultsContainer.innerHTML = `
                    <div class="error-message"></div>
                        <p>ERROR: ${data.error || 'Failed to search courses'}</p>
                    </div>
                `;
                throw new Error(data.error || 'Failed to search courses');
            }
            
            displayResults(data);
        } catch (error) {
            resultsContainer.innerHTML = `
                <div class="error-message">
                    <p>ERROR: ${error.message}</p>
                </div>
            `;
        }
    });
    
    function displayResults(courses) {
        if (!courses || courses.length === 0) {
            resultsContainer.innerHTML = '<div class="no-results">No courses found</div>';
            return;
        }
        
        let resultsHTML = `
            <h2>Search Results</h2>
            <div class="courses-list">
        `;
        
        courses.forEach(course => {
            // Extract data from course object
            const courseInfo = course.course || {};
            const institution = courseInfo.institution || {};
            const characteristics = course.characteristics || {};
            
            resultsHTML += `
                <div class="course-card">
                    <div class="course-header" onclick="this.parentElement.classList.toggle('expanded')">
                        <div class="course-title">
                            <h3>${courseInfo.id || ''} ${courseInfo.name || 'Untitled Course'}</h3>
                            <span class="institution">${institution.name || ''}</span>
                        </div>
                        <div class="expand-icon"></div>
                    </div>
                    
                    <div class="course-details">
                        <!-- Basic Info Section -->
                        <div class="details-section">
                            <h4 class="basic-info">Basic Information</h4>
                            <div class="details-grid">
                                ${characteristics.degree ? `<div class="detail-item"><span>Degree:</span> ${characteristics.degree}</div>` : ''}
                                ${characteristics.duration ? `<div class="detail-item"><span>Duration:</span> ${characteristics.duration}</div>` : ''}
                                ${characteristics.ECTS ? `<div class="detail-item"><span>ECTS:</span> ${characteristics.ECTS}</div>` : ''}
                                ${characteristics.type ? `<div class="detail-item"><span>Type:</span> ${characteristics.type}</div>` : ''}
                                ${characteristics.competition ? `<div class="detail-item"><span>Competition:</span> ${characteristics.competition}</div>` : ''}
                                ${characteristics.current_vacancies ? `<div class="detail-item"><span>Vacancies:</span> ${characteristics.current_vacancies}</div>` : ''}
                            </div>
                        </div>
                        
                        <!-- Entrance Exams Section -->
                        ${renderEntranceExams(course.entrance_exams)}
                        
                        <!-- Classification Section -->
                        ${renderClassificationDetails(course)}
                        
                        <!-- Historical Data (if available) -->
                        ${renderHistoricalData(course.historical_data)}
                        
                        <!-- Course URL -->
                        ${courseInfo.url ? `<div class="course-link"><a href="${courseInfo.url}" target="_blank">Visit Official Course Page</a></div>` : ''}
                    </div>
                </div>
            `;
        });
        
        resultsHTML += '</div>';
        resultsContainer.innerHTML = resultsHTML;
    }
    
    // Helper function to render entrance exams
    function renderEntranceExams(examsData) {
        if (!examsData || !examsData.bundles || examsData.bundles.length === 0) {
            return '';
        }
        
        let html = `<div class="details-section">
            <h4>Entrance Exams</h4>
            <div class="exams-container">`;
            
        if (examsData.is_combination) {
            html += '<p class="exam-note">Requires the first item and one of the items after that:</p>';
        } else if (examsData.is_bundle) {
            html += '<p class="exam-note">Requires two of the following:</p>';
        }
        
        examsData.bundles.forEach((bundle, bundleIndex) => {
            if (bundleIndex > 0 && examsData.is_combination) {
                html += '<div class="exam-separator">AND</div>';
            } else if (bundleIndex > 0) {
                html += '<div class="exam-separator">OR</div>';
            }
            
            html += '<div class="exam-bundle">';
            bundle.exams.forEach(exam => {
                html += `<div class="exam-item"><span class="exam-code">${exam.code}</span> ${exam.name}</div>`;
            });
            html += '</div>';
        });
        
        html += `</div></div>`;
        return html;
    }
    
    // Helper function to render classification details
    function renderClassificationDetails(course) {
        let html = '';
        
        // Min classification
        if (course.min_classification) {
            html += `<div class="details-section">
                <h4>Minimum Classification</h4>
                <div class="details-grid">
                    ${course.min_classification.application_grade ? 
                      `<div class="detail-item"><span>Application Grade:</span> ${course.min_classification.application_grade}</div>` : ''}
                    ${course.min_classification.entrance_exams ? 
                      `<div class="detail-item"><span>Entrance Exams:</span> ${course.min_classification.entrance_exams}</div>` : ''}
                </div>
            </div>`;
        }

        // Prerequisites
        if (course.prerequisites) {
            html += `<div class="details-section">
                <h4>Prerequisites</h4>
                <div class="details-grid">
                    ${course.prerequisites.type ? 
                      `<div class="detail-item"><span>Type:</span> ${course.prerequisites.type}</div>` : ''}
                    ${course.prerequisites.group ? 
                      `<div class="detail-item"><span>Group:</span> ${course.prerequisites.group}</div>` : ''}
                </div>
            </div>`;
        }

        // Calculation formula
        if (course.calculation_formula) {
            html += `<div class="details-section">
                <h4>Calculation Formula</h4>
                <div class="formula-container">
                    ${course.calculation_formula.hs_average ? 
                      `<div class="formula-item">
                         <div class="formula-value">${course.calculation_formula.hs_average}%</div>
                         <div class="formula-label">High School</div>
                       </div>` : ''}
                    ${course.calculation_formula.entrance_exams ? 
                      `<div class="formula-item">
                         <div class="formula-value">${course.calculation_formula.entrance_exams}%</div>
                         <div class="formula-label">Entrance Exams</div>
                       </div>` : ''}
                </div>
            </div>`;
        }
        
        return html;
    }
    
    // Helper function to render historical data
    function renderHistoricalData(historicalData) {
        if (!historicalData || historicalData.length === 0) {
            return '';
        }
        
        let html = `<div class="details-section">
            <h4>Historical Data</h4>
            <div class="historical-data-tabs">`;
            
        // Create year tabs
        html += '<div class="year-tabs">';
        historicalData.forEach((yearData, index) => {
            html += `<button class="year-tab ${index === 0 ? 'active' : ''}" 
                    data-year="${yearData.year}">${yearData.year}</button>`;
        });
        html += '</div>';
        
        // Create content for each year
        html += '<div class="year-content">';
        historicalData.forEach((yearData, index) => {
            html += `<div class="year-panel ${index === 0 ? 'active' : ''}" data-year="${yearData.year}">`;
            
            // Phase tabs
            html += '<div class="phase-tabs">';
            // Don't show Phase 1 if Phase 2 doesn't exist and Phase 1 has no grade (only vacancies)
            if (yearData.phase1 && !(!yearData.phase2 && !yearData.phase1.grade_last)) {
                html += `<button class="phase-tab active" data-phase="1" data-year="${yearData.year}">Phase 1</button>`;
            }
            if (yearData.phase2) {
                html += `<button class="phase-tab ${!yearData.phase1 ? 'active' : ''}" data-phase="2" data-year="${yearData.year}">Phase 2</button>`;
            }
            html += '</div>';
            
            // Phase content
            html += '<div class="phase-content">';
            
            // Phase 1 content
            if (yearData.phase1) {
                html += `<div class="phase-panel active" data-phase="1" data-year="${yearData.year}">`;
                html += renderPhaseData(yearData.phase1);
                html += '</div>';
            }
            
            // Phase 2 content
            if (yearData.phase2) {
                html += `<div class="phase-panel ${!yearData.phase1 ? 'active' : ''}" data-phase="2" data-year="${yearData.year}">`;
                html += renderPhaseData(yearData.phase2);
                html += '</div>';
            }
            
            html += '</div>'; // Close phase-content
            html += '</div>'; // Close year-panel
        });
        html += '</div>'; // Close year-content
        
        html += '</div></div>'; // Close tabs and section
        return html;
    }
    
    // Helper function to render phase data
    function renderPhaseData(phaseData) {
        if (!phaseData) return '';
        
        let html = '<div class="phase-data">';
        
        // Basic phase info
        html += '<div class="phase-stats">';
        if (phaseData.vacancies !== undefined) {
            html += `<div class="stat-item"><span>Vacancies</span>${phaseData.vacancies}</div>`;
        }
        if (phaseData.grade_last) {
            html += `<div class="stat-item"><span>Last Grade</span>${phaseData.grade_last}</div>`;
        }
        html += '</div>';
        
        // Candidates info
        if (phaseData.candidates) {
            html += '<div class="data-group">';
            html += '<h5>Candidates</h5>';
            html += '<div class="data-grid">';
            html += `<div class="data-item"><span>Total</span>${phaseData.candidates.total}</div>`;
            if (phaseData.candidates.fem !== undefined) {
                html += `<div class="data-item"><span>Female</span>${phaseData.candidates.fem}</div>`;
            }
            if (phaseData.candidates.masc !== undefined) {
                html += `<div class="data-item"><span>Male</span>${phaseData.candidates.masc}</div>`;
            }
            if (phaseData.candidates.first_option !== undefined) {
                html += `<div class="data-item"><span>First Option</span>${phaseData.candidates.first_option}</div>`;
            }
            html += '</div></div>';
        }
        
        // Placed info
        if (phaseData.placed) {
            html += '<div class="data-group">';
            html += '<h5>Placed</h5>';
            html += '<div class="data-grid">';
            html += `<div class="data-item"><span>Total</span>${phaseData.placed.total}</div>`;
            if (phaseData.placed.fem !== undefined) {
                html += `<div class="data-item"><span>Female</span>${phaseData.placed.fem}</div>`;
            }
            if (phaseData.placed.masc !== undefined) {
                html += `<div class="data-item"><span>Male</span>${phaseData.placed.masc}</div>`;
            }
            if (phaseData.placed.first_option !== undefined) {
                html += `<div class="data-item"><span>First Option</span>${phaseData.placed.first_option}</div>`;
            }
            html += '</div></div>';
        }
        
        html += '</div>'; // Close phase-data
        return html;
    }
});

// Add event listeners for historical data tabs
document.addEventListener('click', function(e) {
    // Year tab click
    if (e.target.classList.contains('year-tab')) {
        const year = e.target.dataset.year;
        const tabContainer = e.target.closest('.historical-data-tabs');
        
        // Update active tab
        tabContainer.querySelectorAll('.year-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        e.target.classList.add('active');
        
        // Show corresponding panel
        tabContainer.querySelectorAll('.year-panel').forEach(panel => {
            if (panel.dataset.year === year) {
                panel.classList.add('active');
            } else {
                panel.classList.remove('active');
            }
        });
    }
    
    // Phase tab click
    if (e.target.classList.contains('phase-tab')) {
        const phase = e.target.dataset.phase;
        const year = e.target.dataset.year;
        const tabContainer = e.target.closest('.phase-tabs');
        
        // Update active tab
        tabContainer.querySelectorAll('.phase-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        e.target.classList.add('active');
        
        // Show corresponding panel
        const yearPanel = tabContainer.closest('.year-panel');
        yearPanel.querySelectorAll('.phase-panel').forEach(panel => {
            if (panel.dataset.phase === phase && panel.dataset.year === year) {
                panel.classList.add('active');
            } else {
                panel.classList.remove('active');
            }
        });
    }
});