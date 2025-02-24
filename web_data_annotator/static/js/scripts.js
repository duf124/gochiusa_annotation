document.addEventListener("DOMContentLoaded", () => {
    const dynamicForms = document.getElementById("dynamic-forms");
    let activeInput = null;

    // Function to generate form fields for a given category and count,
    // using values already entered (if any) from currentValues,
    // and falling back to initialData if present.
    const generateCategoryForms = (category, count, currentValues = {}) => {
        const group = document.createElement("div");
        group.className = "form-group";
        
        for(let i=1; i<=count; i++) {
            const fieldset = document.createElement("div");
            fieldset.className = "subform";
            
            //const getValue = (field) => initialData[`${category}_${field}_${i}`] || "";
	    // For a given field name, check first for a current value and then for initialData.
            const getValue = (field) => {
                const key = `${category}_${field}_${i}`;
                if (currentValues.hasOwnProperty(key)) {
                    return currentValues[key];
                } else if (initialData && initialData[key] !== undefined) {
                    return initialData[key];
                }
                return "";
            };
            
            let fields = "";
            switch(category) {
                case "balloon":
                    fields = `
                        <div class="form-row">
                        <label>Text: <input type="text" name="balloon_text_${i}" value="${getValue('text')}"></label>
                        <label>Shape: <input type="text" name="balloon_shape_${i}" value="${getValue('shape')}"></label>
                        </div>
                        <div class="form-row">
                        <label>Speaker: <input type="text" name="balloon_speaker_${i}" value="${getValue('speaker')}"></label>
                        <label>Listener: <input type="text" name="balloon_listener_${i}" value="${getValue('listener')}"></label>
                        </div>

                    `;
                    break;
                case "outer":
                    fields = `
                        <div class="form-row">
                        <label>Text: <input type="text" name="outer_text_${i}" value="${getValue('text')}"></label>
                        </div>
                        <div class="form-row">
                        <label>Owner: <input type="text" name="outer_owner_${i}" value="${getValue('owner')}"></label>
                        <label>Type: <input type="text" name="outer_type_${i}" value="${getValue('type')}"></label>
                        </div>
                    `;
                    break;
                case "background":
                    fields = `
                        <div class="form-row">
                        <label>Text: <input type="text" name="background_text_${i}" value="${getValue('text')}"></label>
                        <label>Media: <input type="text" name="background_media_${i}" value="${getValue('media')}"></label>
                        </div>
                    `;
                    break;
                case "character":
                    fields = `
                        <div class="form-row">
                        <label>Who: <input type="text" name="character_who_${i}" value="${getValue('who')}"></label>
                        <label>Face Direction: <input type="text" name="face_direction_${i}" value="${getValue('face_direction')}"></label>
                        </div>
                        <div class="form-row">
                        <label>Behavior_a: <input type="text" name="character_behavior_a_${i}" value="${getValue('behavior_a')}"></label>
                        <label>Behavior_b: <input type="text" name="character_behavior_b_${i}" value="${getValue('behavior_b')}"></label>
                        </div>
                    `;
                    break;
            }
            
            fieldset.innerHTML = `<h4>${category} ${i}</h4>${fields}`;
            group.appendChild(fieldset);
        }
        return group;
    };

    // Update all forms based on radio selections
    const updateAllForms = () => {
	// Gather the current values from all inputs in the dynamic form area.
        const currentValues = {};
        const inputs = dynamicForms.querySelectorAll("input");
        inputs.forEach(input => {
            currentValues[input.name] = input.value;
        });

	// Clear the dynamic forms container.
        dynamicForms.innerHTML = "";
        
        const counts = {
            balloon: parseInt(document.querySelector('input[name="balloon_num"]:checked')?.value || 0),
            outer: parseInt(document.querySelector('input[name="outer_num"]:checked')?.value || 0),
            background: parseInt(document.querySelector('input[name="background_num"]:checked')?.value || 0),
            character: parseInt(document.querySelector('input[name="character_num"]:checked')?.value || 0)
        };
        
        Object.entries(counts).forEach(([category, count]) => {
            //if(count > 0) dynamicForms.appendChild(generateCategoryForms(category, count));
	    if(count > 0) dynamicForms.appendChild(generateCategoryForms(category, count, currentValues));
        });
    };

    // Set initial radio states
    const setInitialRadios = () => {
        Object.entries(initialValues).forEach(([name, value]) => {
            const radio = document.querySelector(`input[name="${name}"][value="${value}"]`);
            if(radio) radio.checked = true;
        });
    };

    // Event listeners
    document.querySelectorAll('input[type="radio"]').forEach(radio => {
        radio.addEventListener("change", updateAllForms);
    });

    document.getElementById("annotation-form").addEventListener("focusin", (e) => {
        if(e.target.matches("input")) activeInput = e.target;
    });

    document.querySelectorAll(".shortcut-button").forEach(button => {
        button.addEventListener("click", () => {
            if(activeInput) activeInput.value += button.textContent;
        });
    });

    // Initial setup
    setInitialRadios();
    updateAllForms();
});
