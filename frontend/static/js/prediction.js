// Prediction Module Client-Side Script
// Manages symptom search, tags list, form submission, and results dashboard.

document.addEventListener("DOMContentLoaded", function() {
    setupSymptomSearch();
    setupFormSubmission();
    setupResetBtn();
});

// Selected symptoms array (state tracker)
let selectedSymptoms = [];

// Autocomplete dropdown matching logic
function setupSymptomSearch() {
    const searchInput = document.getElementById("symptomSearch");
    const dropdown = document.getElementById("symptomsDropdown");
    
    if (!searchInput || !dropdown) return;
    
    let highlightedIndex = -1;
    let filteredList = [];

    searchInput.addEventListener("input", function() {
        const query = searchInput.value.trim().lowerCaseOrStandard();
        dropdown.innerHTML = "";
        highlightedIndex = -1;
        
        if (!query) {
            dropdown.style.display = "none";
            return;
        }
        
        // Filter out symptoms that are already selected, and match search query
        filteredList = ALL_SYMPTOMS.filter(symptom => 
            symptom.includes(query) && !selectedSymptoms.includes(symptom)
        ).slice(0, 8); // limit to 8 suggestions
        
        if (filteredList.length === 0) {
            dropdown.style.display = "none";
            return;
        }
        
        dropdown.style.display = "block";
        filteredList.forEach((symptom, idx) => {
            const item = document.createElement("div");
            item.className = "dropdown-item";
            item.innerText = symptom;
            
            item.addEventListener("click", function() {
                addSymptomTag(symptom);
                searchInput.value = "";
                dropdown.style.display = "none";
            });
            
            dropdown.appendChild(item);
        });
    });

    // Helper extension to handle browser safe string comparison
    String.prototype.lowerCaseOrStandard = function() {
        return this.toLowerCase();
    };

    // Keyboard navigation in dropdown
    searchInput.addEventListener("keydown", function(e) {
        const items = dropdown.querySelectorAll(".dropdown-item");
        if (dropdown.style.display !== "block" || items.length === 0) return;
        
        if (e.key === "ArrowDown") {
            e.preventDefault();
            highlightedIndex = (highlightedIndex + 1) % items.length;
            updateHighlight(items);
        } else if (e.key === "ArrowUp") {
            e.preventDefault();
            highlightedIndex = (highlightedIndex - 1 + items.length) % items.length;
            updateHighlight(items);
        } else if (e.key === "Enter") {
            e.preventDefault();
            if (highlightedIndex >= 0 && highlightedIndex < items.length) {
                items[highlightedIndex].click();
            } else if (items.length > 0) {
                items[0].click(); // default to first match
            }
        } else if (e.key === "Escape") {
            dropdown.style.display = "none";
        }
    });

    // Highlight class toggling
    function updateHighlight(items) {
        items.forEach((item, idx) => {
            if (idx === highlightedIndex) {
                item.classList.add("highlighted");
                item.scrollIntoView({ block: "nearest" });
            } else {
                item.classList.remove("highlighted");
            }
        });
    }

    // Close dropdown on outside click
    document.addEventListener("click", function(e) {
        if (e.target !== searchInput && e.target !== dropdown) {
            dropdown.style.display = "none";
        }
    });
}

// Add a symptom tag to the list and update UI
function addSymptomTag(symptom) {
    if (selectedSymptoms.includes(symptom)) return;
    
    selectedSymptoms.push(symptom);
    
    const container = document.getElementById("selectedSymptoms");
    const placeholder = container.querySelector(".no-symptoms-placeholder");
    if (placeholder) placeholder.style.display = "none";
    
    const tag = document.createElement("span");
    tag.className = "symptom-tag";
    tag.id = `tag-${symptom.replace(/\s+/g, '-')}`;
    tag.innerHTML = `
        <span>${symptom}</span>
        <button type="button" class="remove-tag-btn" onclick="removeSymptomTag('${symptom}')">&times;</button>
    `;
    
    container.appendChild(tag);
    updateSymptomState();
}

// Remove a symptom tag and update UI
window.removeSymptomTag = function(symptom) {
    selectedSymptoms = selectedSymptoms.filter(item => item !== symptom);
    
    const tag = document.getElementById(`tag-${symptom.replace(/\s+/g, '-')}`);
    if (tag) tag.remove();
    
    updateSymptomState();
};

// Check if tags list is empty, update count, and enable/disable submit button
function updateSymptomState() {
    const countLabel = document.getElementById("symptomCount");
    const submitBtn = document.getElementById("submitBtn");
    const container = document.getElementById("selectedSymptoms");
    const placeholder = container.querySelector(".no-symptoms-placeholder");
    
    if (countLabel) countLabel.innerText = selectedSymptoms.length;
    
    if (selectedSymptoms.length > 0) {
        if (submitBtn) submitBtn.disabled = false;
        if (placeholder) placeholder.style.display = "none";
    } else {
        if (submitBtn) submitBtn.disabled = true;
        if (placeholder) placeholder.style.display = "block";
    }
}

// Intercept form submission and run AJAX ML classification
function setupFormSubmission() {
    const form = document.getElementById("predictionForm");
    const submitBtn = document.getElementById("submitBtn");
    const btnText = document.getElementById("btnText");
    const btnLoading = document.getElementById("btnLoading");
    
    const consolePlaceholder = document.getElementById("consolePlaceholder");
    const consoleResultPanel = document.getElementById("consoleResultPanel");
    
    if (!form) return;
    
    form.addEventListener("submit", function(e) {
        e.preventDefault();
        
        if (selectedSymptoms.length === 0) return;
        
        // Show loading state
        submitBtn.disabled = true;
        btnText.classList.add("hidden");
        btnLoading.classList.remove("hidden");
        
        // Send request to Flask API
        fetch('/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ symptoms: selectedSymptoms })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error("Diagnostic prediction server failed.");
            }
            return response.json();
        })
        .then(data => {
            // Render results
            document.getElementById("resultDisease").innerText = data.predicted_disease;
            
            // Format confidence score
            const confVal = data.confidence_score;
            const pct = confVal <= 1.0 ? confVal * 100 : confVal;
            document.getElementById("resultConfidenceText").innerText = `${pct.toFixed(1)}%`;
            document.getElementById("resultConfidenceBar").style.width = `${pct}%`;
            
            document.getElementById("resultDesc").innerText = data.description;
            document.getElementById("resultSpecialist").innerText = data.specialist;
            
            // Precaution List
            const precList = document.getElementById("resultPrecautions");
            precList.innerHTML = "";
            if (data.precautions && data.precautions.length > 0) {
                data.precautions.forEach(p => {
                    const li = document.createElement("li");
                    li.innerText = p;
                    precList.appendChild(li);
                });
            } else {
                precList.innerHTML = "<li>No specific precautions recorded.</li>";
            }
            
            // Causes List
            const causesList = document.getElementById("resultCauses");
            causesList.innerHTML = "";
            if (data.causes && data.causes.length > 0) {
                data.causes.forEach(c => {
                    const li = document.createElement("li");
                    li.innerText = c;
                    causesList.appendChild(li);
                });
            } else {
                causesList.innerHTML = "<li>No causes listed.</li>";
            }
            
            // Diet Guidelines
            const dietText = data.diet && data.diet.length > 0 ? data.diet.join(", ") : "Maintain standard hydrating nutrition.";
            document.getElementById("resultDiet").innerText = dietText;
            
            // Exercises Guidelines
            const execText = data.exercises && data.exercises.length > 0 ? data.exercises.join(", ") : "Gentle walking as tolerated.";
            document.getElementById("resultExercises").innerText = execText;
            
            // Download PDF Report Link
            const reportBtn = document.getElementById("downloadReportBtn");
            if (reportBtn) {
                reportBtn.href = `/report/${data.prediction_id}`;
            }
            
            // Show result panel and hide placeholder
            consolePlaceholder.classList.add("hidden");
            consoleResultPanel.classList.remove("hidden");
            
            // Scroll to results console on mobile
            document.getElementById("resultsConsole").scrollIntoView({ behavior: 'smooth' });
        })
        .catch(err => {
            console.error("Inference Error:", err);
            alert(`Error: ${err.message}. Please check application connectivity.`);
        })
        .finally(() => {
            // Restore button state
            submitBtn.disabled = false;
            btnText.classList.remove("hidden");
            btnLoading.classList.add("hidden");
        });
    });
}

// Reset scan action
function setupResetBtn() {
    const clearBtn = document.getElementById("clearBtn");
    const consolePlaceholder = document.getElementById("consolePlaceholder");
    const consoleResultPanel = document.getElementById("consoleResultPanel");
    
    if (!clearBtn) return;
    
    clearBtn.addEventListener("click", function() {
        // Clear state
        selectedSymptoms = [];
        document.getElementById("selectedSymptoms").innerHTML = '<span class="no-symptoms-placeholder">No symptoms selected. Start typing in the search box above.</span>';
        updateSymptomState();
        
        // Reset Search Input
        const searchInput = document.getElementById("symptomSearch");
        if (searchInput) searchInput.value = "";
        
        // Toggle view
        consoleResultPanel.classList.add("hidden");
        consolePlaceholder.classList.remove("hidden");
    });
}
