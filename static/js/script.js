document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.querySelector('form[action="/search"]');
    const searchInput = document.getElementById('basic-name');
    const resultsContainer = document.querySelector('.results-section');
    const advancedSearchToggle = document.getElementById('advanced-search-toggle');
    const basicSearchBar = document.getElementById('search-bar');
    const advancedSearch = document.getElementById('advanced-search');
    const advancedSearchForm = document.getElementById('advanced-search-form');
    const sortBySelect = document.getElementById('sort_by');
    const gradeSortOptions = document.getElementById('grade_sort_options');
    
    advancedSearchToggle.addEventListener('click', function() {
        basicSearchBar.classList.toggle('hidden');
        advancedSearch.classList.toggle('hidden');
        
        if (advancedSearch.classList.contains('hidden')) {
            advancedSearchToggle.textContent = 'Advanced Mode';
        } else {
            advancedSearchToggle.textContent = 'Simple Mode';
        }
    });

    // Handle operator changes
    const operatorSelects = document.querySelectorAll('.operator-select');
    operatorSelects.forEach(select => {
        select.addEventListener('change', function() {
            const rangeInputs = this.nextElementSibling;
            const maxInput = rangeInputs.querySelector('input[id$="_max"]');
            
            if (this.value === 'between') {
                maxInput.classList.remove('hidden');
            } else {
                maxInput.classList.add('hidden');
            }
        });
    });

    const url = new URL(window.location.href);
    if (url.searchParams.has('search')) {
        const searchQuery = url.searchParams.get('search');
        const searchParams = new URLSearchParams();
        searchParams.append('course_name', searchQuery);

        search(searchParams);
    }
    
    advancedSearchForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(advancedSearchForm);
        const searchParams = new URLSearchParams();
        
        for (const [key, value] of formData.entries()) {
            if (value) {
                searchParams.append(key, value);
            }
        }

        await search(searchParams);
    });

    searchForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const searchQuery = searchInput.value.trim();
        if (!searchQuery) return;

        const searchParams = new URLSearchParams();
        searchParams.append('course_name', searchQuery);
        
        await search(searchParams);
    });

    async function search(searchParams) {
        // Show loading state
        resultsContainer.innerHTML = '<div class="loading">Searching courses...</div>';
        
        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: searchParams.toString()
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
    }
    
    function displayResults(courses) {
        if (!courses || courses.length === 0) {
            resultsContainer.innerHTML = '<div class="no-results">No courses found</div>';
            return;
        }
        
        let resultsHTML = `
            <h2>Search Results</h2>
            <div class="courses-list">
        `;
        let counter = 0;

        courses.forEach(course => {
            // Extract data from course object
            const courseInfo = course.course || {};
            const institution = courseInfo.institution || {};
            const characteristics = course.characteristics || {};
            counter += 1;
            
            resultsHTML += `
                <div class="course-card" id="course-${counter}">
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
                                ${course.id ? `<div class="detail-item"><span>Unique ID:</span> ${course.id}</div>` : ''}
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
                      `<div class="detail-item"><span>Group:</span> <a href="https://www.dges.gov.pt/guias/preq_grupo.asp?pr=${course.prerequisites.group}">${course.prerequisites.group}</a></div>` : ''}
                </div>
            </div>`;
        }

        // Calculation formula
        if (course.calculation_formula) {
            html += `<div class="details-section">
                <h4>Calculation Formula</h4>
                <div class="details-grid">
                    ${course.calculation_formula.hs_average ? 
                      `<div class="detail-item"><span>High School:</span> ${course.calculation_formula.hs_average}%</div>` : ''}
                    ${course.calculation_formula.entrance_exams ? 
                      `<div class="detail-item"><span>Entrance Exams:</span> ${course.calculation_formula.entrance_exams}%</div>` : ''}
                </div>
            </div>`;
        }

        // Regional preferences
        if (course.regional_preferences) {
            html += `<div class="details-section">
                <h4>Regional Preferences</h4>
                <div class="details-grid">
                    ${course.regional_preferences.percentage ? 
                      `<div class="detail-item"><span>Percentage:</span> ${course.regional_preferences.percentage}</div>` : ''}
                </div>
                    ${course.regional_preferences.regions ? 
                        `<div class="detail-item"><span>Regions:</span> ${course.regional_preferences.regions.join(', ')}</div>` : ''}
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
        
        // Basic phase info - always show vacancies and grade (even if grade is 0/null)
        html += '<div class="phase-stats">';
        html += `<div class="stat-item"><span>Vacancies</span>${phaseData.vacancies !== undefined ? phaseData.vacancies : 'N/A'}</div>`;
        html += `<div class="stat-item"><span>Last Grade</span>${phaseData.grade_last !== undefined && phaseData.grade_last !== null ? phaseData.grade_last : 'N/A'}</div>`;
        html += '</div>';
        
        // Candidates info
        if (phaseData.candidates) {
            html += '<div class="data-group">';
            html += '<h5>Candidates</h5>';
            html += '<div class="data-grid">';
            html += `<div class="data-item"><span>Total</span>${phaseData.candidates.total}</div>`;
            html += `<div class="data-item"><span>Female</span>${phaseData.candidates.fem !== undefined ? phaseData.candidates.fem : 'N/A'}</div>`;
            html += `<div class="data-item"><span>Male</span>${phaseData.candidates.masc !== undefined ? phaseData.candidates.masc : 'N/A'}</div>`;
            html += `<div class="data-item"><span>First Option</span>${phaseData.candidates.first_option !== undefined ? phaseData.candidates.first_option : 'N/A'}</div>`;
            html += '</div></div>';
        }
        
        // Placed info
        if (phaseData.placed) {
            html += '<div class="data-group">';
            html += '<h5>Placed</h5>';
            html += '<div class="data-grid">';
            html += `<div class="data-item"><span>Total</span>${phaseData.placed.total}</div>`;
            html += `<div class="data-item"><span>Female</span>${phaseData.placed.fem !== undefined ? phaseData.placed.fem : 'N/A'}</div>`;
            html += `<div class="data-item"><span>Male</span>${phaseData.placed.masc !== undefined ? phaseData.placed.masc : 'N/A'}</div>`;
            html += `<div class="data-item"><span>First Option</span>${phaseData.placed.first_option !== undefined ? phaseData.placed.first_option : 'N/A'}</div>`;
            html += '</div></div>';
        }
        
        // Average grades - add this section to display averages
        if (phaseData.averages) {
            html += '<div class="data-group">';
            html += '<h5>Average Grades</h5>';
            html += '<div class="data-grid">';
            html += `<div class="data-item"><span>Application</span>${phaseData.averages.application_grade !== undefined ? phaseData.averages.application_grade : 'N/A'}</div>`;
            html += `<div class="data-item"><span>Entrance Exams</span>${phaseData.averages.entrance_exams !== undefined ? phaseData.averages.entrance_exams : 'N/A'}</div>`;
            html += `<div class="data-item"><span>High School</span>${phaseData.averages.hs_average !== undefined ? phaseData.averages.hs_average : 'N/A'}</div>`;
            html += '</div></div>';
        }
        
        html += '</div>'; // Close phase-data
        return html;
    }
    
    function toggleGradeSortOptions() {
        if (sortBySelect.value === 'grade_asc' || sortBySelect.value === 'grade_desc' || 
            sortBySelect.value === 'average_asc' || sortBySelect.value === 'average_desc'
        ) {
            gradeSortOptions.style.display = 'block';
        } else {
            gradeSortOptions.style.display = 'none';
        }
    }
    
    // Initial toggle
    toggleGradeSortOptions();
    
    // Toggle on change
    sortBySelect.addEventListener('change', toggleGradeSortOptions);
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