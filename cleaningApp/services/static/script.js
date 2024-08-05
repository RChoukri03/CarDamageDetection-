// const apiBaseUrl = 'http://ec2-13-36-237-112.eu-west-3.compute.amazonaws.com:4000/';
const apiBaseUrl = 'http://localhost:4000/';

let isPendingMode = false;
let isCheckMode = false;
let rotationDegrees = 0;
let rotationApplied = false;

document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM fully loaded and parsed");
    attachEventListeners();
    updateStatusInfo();
});

document.addEventListener('DOMContentLoaded', function() {
    var validatorNameInput = document.getElementById('validatorName');

    function toUpperCaseInput() {
      validatorNameInput.value = validatorNameInput.value.toUpperCase();
    }

    validatorNameInput.addEventListener('input', toUpperCaseInput);

    toUpperCaseInput();
  });

function attachEventListeners() {
    document.getElementById('rotateButton').addEventListener('click', rotateImage);
    document.getElementById('imageDisplay').addEventListener('click', toggleFullscreen);
    document.getElementById('validatorName').addEventListener('input', toggleStartButton);
    document.getElementById('startProcess').addEventListener('click', startValidationProcess);
    document.getElementById('validateButton').addEventListener('click', validateData);
    document.getElementById('nextButton').addEventListener('click', handleNextButtonClick);
    document.getElementById('skipButton').addEventListener('click', skipToNextState);
    document.getElementById('modeSwitch').addEventListener('change', toggleMode);
    document.getElementById('checkSwitch').addEventListener('change', toggleCheckMode);
    document.getElementById('validateAsNotACarButton').addEventListener('click', validateAsNotACar);
    document.getElementById('resetButton').addEventListener('click', ResetData);
}

function rotateImage() {
    const imageElement = document.querySelector('#imageDisplay img');
    rotationDegrees += 90;
    rotationDegrees %= 360;
    imageElement.style.transform = `rotate(${rotationDegrees}deg)`;
    rotationApplied = true;
}

function toggleFullscreen(event) {
    const img = event.target;
    img.classList.toggle('fullscreen');
}

function validateRotation() {
    const imageName = document.getElementById('dataDisplay').getAttribute('data-imageName');
    axios.post(`${apiBaseUrl}/validateRotation`, { imageName, rotationDegrees })
        .then(() => {})
        .catch(error => console.error('Error saving rotation:', error));
}

function toggleStartButton() {
    document.getElementById('startProcess').disabled = this.value.trim() === '';
}

function startValidationProcess() {
    const validatorName = document.getElementById('validatorName').value.trim();
    if (!validatorName) {
        alert('Please enter a validator name to start.');
        return;
    }

    enableButtons();
    getNextKeyAndLoadData(isCheckMode ? 'validated' : (isPendingMode ? 'pending' : 'initial'));
    const toggleDataButton = document.getElementById('toggleDataButton');
    toggleDataButton.style.display = 'block';
    const svgImage = document.getElementById('carImage');
    svgImage.style.display = 'block';  // Change display from 'none' to 'block'
}

function enableButtons() {
    document.querySelectorAll('button').forEach(button => button.disabled = false);
    if (isCheckMode) {
        document.getElementById('validateButton').disabled = true;
    }
}

function handleNextButtonClick() {
    const validatorName = document.getElementById('validatorName').value.toUpperCase();
    moveToNextState(() => {
        incrementValidatorCount(validatorName);
        // updateStatusInfo();
        document.getElementById('nextButton').disabled = true;
        fetchCountAndDisplay(validatorName)
    });
}

function incrementValidatorCount(validatorName) {
    var validatorName = validatorName.toUpperCase()
    fetch(`${apiBaseUrl}/incrementValidatorCount`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ validatorName })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            console.log('Count incremented successfully.');
            fetchCountAndDisplay(validatorName)
            updateValidatorCountDisplay(data.count);
        } else {
            console.error('Failed to increment count:', data.message);
        }
    })
    .catch(error => console.error('Error incrementing validator count:', error));
}

function moveToNextState(callback) {
    const imageName = document.getElementById('dataDisplay').getAttribute('data-imageName');
    const nextUrl = isPendingMode ? `${apiBaseUrl}/moveImageToValidated` : `${apiBaseUrl}/moveImageToPending`;
    axios.post(nextUrl, { imageName })
        .then(() => {
            callback && callback();
            getNextKeyAndLoadData(isPendingMode ? 'pending' : 'initial');
        })
        .catch(error => console.error('Error moving to the next state:', error));
}


document.addEventListener('DOMContentLoaded', function() {
    const toggleButton = document.querySelector('.toggle-button');
    const images = document.querySelectorAll('.static-img');

    toggleButton.addEventListener('click', function() {
        images.forEach(img => {
            if (img.style.display === 'none') {
                img.style.display = 'block';
            } else {
                img.style.display = 'none';
            }
        });
    });
});


function getNextKeyAndLoadData(mode) {
    axios.get(`${apiBaseUrl}/getnextKeyIn${capitalizeFirstLetter(mode)}`)
        .then(response => {

            const key = response.data.key;
            if (key) loadData(key, mode);
            else showToast('No more keys available!');
        })
        .catch(error => console.error('Error getting next key:', error));
}

function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}

function loadData(imageName, mode) {
    console.log("Loading data...");
    axios.get(`${apiBaseUrl}/getImgUrl/${imageName}`)
        .then(response => {
            console.log("Image URL retrieved successfully.");
            if (response.data.url) {
                const imgUrl = response.data.url;
                document.getElementById('imageDisplay').innerHTML = `<img src="${imgUrl}" alt="Loaded Image" class="img-fluid">`;
                document.getElementById('dataDisplay').setAttribute('data-imageName', imageName);
                fetchData(imageName, mode);
            } else {
                console.error('Error: Image URL not found.');
                getNextKeyAndLoadData(mode); // Passer à la prochaine clé/image
            }
        })
        .catch(error => {
            console.error('Error getting image URL:', error);
            getNextKeyAndLoadData(mode); // Passer à la prochaine clé/image
        });
}



function generateInputElement(key, value, readOnly) {
    return `<div class="col-md-3 mb-3">
                <label class="form-label label-blue">${key}</label>
                <input type="text" class="form-control sync-input"
                       id="${key}-input" name="${key}"
                       value="${value}" ${readOnly}
                       data-sync-id="${key}-input">
            </div>`;
}

function fetchData(imageName, mode) {
    console.log("Fetching data...");
    const dataUrl = `${apiBaseUrl}/getDataFrom${capitalizeFirstLetter(mode)}`;
    let count = 0;
    // let topDataHtml = '';
    axios.post(dataUrl, { imageName: imageName })
        .then(response => {
            console.log("Data fetched successfully.");
            const data = response.data.data;
            let dataHtml = '';
            const orderedKeys = [
                "Aile avant droit", "Porte avant droite", "Porte arriere droite", "Aile arriere droit",
                "Feux avant droit", "Feux arriere droit", "Feux avant gauche", "Feux arriere gauche",
                "Aile avant gauche", "Porte avant gauche", "Porte arriere gauche", "Aile arriere gauche",
                "Pare-choc", "Plaque d\'immat avant", "Pare-choc arriere", "Plaque d\'immat arriere",
                "Pare-brise avant", "Pare-brise arriere", "Capot", "Malle",
                "Rejet", "carOrNot", "validatorName"
            ];

            orderedKeys.forEach(key => {
                if (data.hasOwnProperty(key)) {
                    console.log(`Processing key: ${key}`);
                    const value = data[key];

                    const readOnly = (mode === 'validated' || key === 'validatorName') ? 'readonly' : '';
                    const highlightClass = (value && value !== 0) ? 'highlight' : '';

                    let inputElement = '';

                    if (key === 'nomImage' || key === 'validatorName') {
                        inputElement = `<div class="col-md-3 mb-3">
                                            <label class="form-label label-blue">${key}</label>
                                            <input type="text" class="form-control" name="${key}" value="${value}" readonly>
                                        </div>`;
                    } else if (key === 'Rejet' || key === 'carOrNot') {
                        const checkedClass = value === 1 ? 'checked' : '';
                        inputElement = `<div class="col-md-3 mb-3 toggle-container ${checkedClass}" onclick="toggleCheckbox('${key}')">
                                            <label class="form-label label-blue">${key}</label>
                                            <input type="checkbox" class="form-check-input" name="${key}"
                                                ${value === 1 ? 'checked' : ''} value="${value === 1 ? 1 : 0}" hidden>
                                        </div>`;
                    }
                    else if (orderedKeys.includes(key)) {
                        inputElement = generateLampInput(key, value);

                    } else {
                        // Générer l'élément d'entrée de texte pour la clé
                        inputElement = `<div class="col-md-3 mb-3">
                                            <label class="form-label label-blue">${key}</label>
                                            <input type="text" class="form-control ${highlightClass}" name="${key}" value="${value}" ${readOnly}>
                                        </div>`;
                    }

                    if (count % 4 === 0) dataHtml += '<div class="row">';
                    dataHtml += inputElement;
                    count++;
                    if (count % 4 === 0) dataHtml += '</div>';
                }
            });
            if (count % 4 !== 0) dataHtml += '</div>';
            document.getElementById('dataDisplay').innerHTML = dataHtml;
            updateButtonColors(data);
        })
        .catch(error => {
            console.error('Error getting data:', error);
        });
}

function updateButtonColors(data) {
    createImageMap();
    createElements();

    const orderedKeys = [
        "Aile avant droit", "Porte avant droite", "Porte arriere droite", "Aile arriere droit",
        "Feux avant droit", "Feux arriere droit", "Feux avant gauche", "Feux arriere gauche",
        "Aile avant gauche", "Porte avant gauche", "Porte arriere gauche", "Aile arriere gauche",
        "Pare-choc", "Plaque d\'immat avant", "Pare-choc arriere", "Plaque d\'immat arriere",
        "Pare-brise avant", "Pare-brise arriere", "Capot", "Malle"
    ];

    orderedKeys.forEach(key => {
        const normalizedKey = cleanKeyForId(key);
        const value = data[normalizedKey];
        console.log(`Checking element: ${normalizedKey}, value: ${value}`); // Log pour débogage

        const buttonElement = document.getElementById(normalizedKey);
        const area = document.querySelector(`area[data-key="${key}"]`);
        if (buttonElement) {
            buttonElement.classList.remove('level-1', 'level-2', 'level-3');
            if (value > 0 && value <= 3) {
                buttonElement.classList.add(`level-${value}`);
                if (area) {
                    area.className = '';
                    area.classList.add(`zone-level-${value}`);
                }
            }
        } else {
            console.warn(`Element with ID '${normalizedKey}' not found. Check if it's created and added to DOM correctly.`);
        }
        refreshSVGArea(key, value)
    });
}



function cleanKeyForId(key) {
    return key //.replace(/'/g, "\\'"); //capitalizeFirstLetter(key.replace(/\s+/g, '_').toLowerCase()); // Remplacer les espaces par des underscores et mettre en minuscules
}

function toggleDataDisplay() {
    const dataDisplay = document.getElementById('dataDisplay');
    dataDisplay.style.display = dataDisplay.style.display === 'none' ? 'block' : 'none';
}

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('area').forEach(area => {
        area.addEventListener('click', function(event) {
            event.preventDefault();
            let part = cleanKeyForId(this.dataset.key);
            updateDataForPart(part);
        });
    });
});




function updateLampValue(key, level, event) {
    //key = key.replace(/'/g, "\\'")
    event.preventDefault();
    console.log('generat',key,'with level', level,'event',event);
    const lamps = event.currentTarget.parentNode.querySelectorAll('.lamp');
    const input = document.querySelector(`input[name="${key}"]`);
    lamps.forEach(lamp => {
        lamp.classList.remove('active', 'level-1', 'level-2', 'level-3');
    });

    let currentLevel = parseInt(input.value);
    let newLevel = level;

    if (currentLevel === level) {
        newLevel = 0; // Unselect if the same level is clicked
    } else {
        // Activer la nouvelle sélection
        const selectedLamp = Array.from(lamps).find(lamp => parseInt(lamp.textContent, 10) === level);
        if (selectedLamp) {
            selectedLamp.classList.add('active', `level-${level}`);
        }
    }

    input.value = newLevel;
}





function toggleCheckbox(key) {
    const checkbox = document.querySelector(`input[name="${key}"]`);
    const container = checkbox.closest('.toggle-container');

    // Bascule l'état checked du checkbox
    checkbox.checked = !checkbox.checked;

    // Met à jour la valeur du checkbox en fonction de son état
    checkbox.value = checkbox.checked ? 1 : 0;

    // Bascule la classe 'checked' pour le conteneur en fonction de l'état du checkbox
    container.classList.toggle('checked', checkbox.checked);
}
document.getElementById('startProcess').addEventListener('click', function() {
    var validatorName = document.getElementById('validatorName').value.toUpperCase();
    if (validatorName) {
        fetchCountAndDisplay(validatorName);
        setInterval(() => {
            fetchCountAndDisplay(validatorName);
        }, 900000);
    } else {
        alert('Please enter a validator name.');
    }
});

function fetchCountAndDisplay(validatorName) {
    var validatorName = validatorName.toUpperCase()
    fetch(`${apiBaseUrl}/getValidatorCount`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ validatorName })
    })
    .then(response => response.json())
    .then(data => {
        const count = data.count;
        const countDisplay = document.getElementById('validationCount');
        countDisplay.textContent =  count;

        countDisplay.style.color = getColorForCount(count)
    })
    .catch(error => {
        console.error('Error fetching validator count:', error);
        const countDisplay = document.getElementById('validationCount');
        countDisplay.textContent = '-1000';
        countDisplay.style.color = 'red';
    });
}

function getColorForCount(count) {
    const minCount = -1500;
    const maxCount = 500;

    // Normaliser count entre 0 et 1
    let normalizedCount = (count - minCount) / (maxCount - minCount);
    normalizedCount = Math.max(0, Math.min(1, normalizedCount)); // Assurer que la valeur est entre 0 et 1

    // Calculer la couleur
    // Rouge diminue tandis que Vert augmente
    const red = 255 * (1 - normalizedCount);
    const green = 255 * normalizedCount;
    const blue = 0; // Pas de composante bleue

    // Retourner la couleur formatée en RGB
    return `rgb(${Math.round(red)}, ${Math.round(green)}, ${blue})`;}



function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}

function updateStatusInfo() {
    fetch(`${apiBaseUrl}/getStatus`)
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            ['allCleanedImages', 'notVerifiedImages', 'pendingImages', 'validatedImages'].forEach(key => {
                const element = document.getElementById(key);
                if (element) {
                    element.textContent = data[key];
                } else {
                    console.error('Element not found for key:', key);
                }
            });
        } else {
            console.error('Error fetching status:', data.message);
        }
    })
    .catch(error => console.error('Error loading status:', error));
}


function showToast(message) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => {
        toast.classList.replace('show', 'hide');
        setTimeout(() => {
            toast.classList.remove('hide');
        }, 500);
    }, 3000);
}


function updateValidatorCountDisplay(count) {
    const countDisplay = document.getElementById('validationCount');
    countDisplay.textContent = ` ${count}`;
    applyColorCoding(count);
}

function applyColorCoding(count) {
    const countDisplay = document.getElementById('validationCount');
    if (count >= 500) {
        countDisplay.style.color = 'green';
    } else if (count <= -1500) {
        countDisplay.style.color = 'red';
    } else {
        countDisplay.style.color = 'orange';
    }
}

function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}



function toggleMode() {
    isPendingMode = this.checked;
    disableAllExceptStart();
    resetInterface();
}

function toggleCheckMode() {
    isCheckMode = this.checked;
    disableAllExceptStart();
    resetInterface();
}

function disableAllExceptStart() {
    document.querySelectorAll('button:not(#startProcess)').forEach(button => button.disabled = true);
}

function resetInterface() {
    document.getElementById('imageDisplay').innerHTML = '';
    document.getElementById('dataDisplay').innerHTML = '';
    document.getElementById('dataDisplay').removeAttribute('data-imageName');
}

function addSyncEventListeners() {
    document.querySelectorAll('.sync-input').forEach(input => {
        input.addEventListener('input', (event) => {
            const syncId = event.target.dataset.syncId;
            document.querySelectorAll(`[data-sync-id="${syncId}"]`).forEach(syncInput => {
                if (syncInput !== event.target) {
                    syncInput.value = event.target.value;
                }
            });
        });
    });
}

function validateData() {
    const dataDisplay = document.getElementById('dataDisplay');
    const imageName = dataDisplay.getAttribute('data-imageName');
    const validatorName = document.getElementById('validatorName').value.toUpperCase();
    if (!imageName) {
        console.error('Image name is missing!');
        alert('Image name is missing!');
        return;
    }
    if (!validatorName) {
        alert('Validator name is required!');
        return;
    }
    const inputs = document.querySelectorAll('#dataDisplay input');
    let newData = { validatorName };
    inputs.forEach(input => {
        newData[input.name] = input.value;
    });
    const updateUrl = `${apiBaseUrl}/updateImageIn${isPendingMode ? 'Pending' : 'Initial'}`;
    axios.post(updateUrl, { imageName: imageName, newData: newData })
        .then(response => {
            if (rotationApplied) {
                validateRotation(imageName, rotationDegrees);
                showToast('Data and image orientation Updated Successfully!');
            } else {
                showToast('Data Updated Successfully!');
            }

            document.getElementById('nextButton').disabled = false;
        })
        .catch(error => {
            console.error('Error updating data:', error);
            alert('Failed to update data. Please try again!');
        });
}
function skipToNextState() {
    if (isCheckMode) {
        getNextKeyAndLoadData('validated');
    }
    else if (isPendingMode) {
        getNextKeyAndLoadData('pending');
    } else {
        getNextKeyAndLoadData('initial');
    }
}

function updateValidationCount() {
    fetch(`${apiBaseUrl}/getValidatorCount`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ validatorName: document.getElementById('validatorName').value.toUpperCase() })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            const countDisplay = document.getElementById('validationCount');
            countDisplay.textContent = data.count;
            if (data.count >= 500) {
                countDisplay.style.color = 'green';
            } else if (data.count <= -1500) {
                countDisplay.style.color = 'red';
            } else {
                countDisplay.style.color = 'orange';
            }
        } else {
            console.error('Error fetching validator count:', data.message);
        }
    })
    .catch(error => console.error('Error fetching validator count:', error));
}

document.addEventListener('DOMContentLoaded', function() {
        const statusCollapse = document.getElementById('statusCollapse');

        statusCollapse.addEventListener('show.bs.collapse', function () {
            axios.get('/getStatus')
                .then(response => {
                    const data = response.data;
                    document.getElementById('allCleanedImages').textContent = data.AllCleanedImages;
                    document.getElementById('notVerifiedImages').textContent = data.NotverifiedImages;
                    document.getElementById('pendingImages').textContent = data.PendingImages;
                    document.getElementById('validatedImages').textContent = data.validatedImages;
                })
                .catch(error => console.error('Error loading status:', error));
        });
    });




document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('area').forEach(area => {
        area.addEventListener('click', function(event) {
            event.preventDefault();
            let part = this.dataset.key;
            updateDataForPart(part);
        });
    });
});



function updateButtonColor(key, level) {
    const button = document.querySelector(`button[data-key="${key}"]`);
    if (!button) return;
    button.classList.remove('btn-success', 'btn-warning', 'btn-danger');
    if (level === 1) {
        button.classList.add('btn-success');
    } else if (level === 2) {
        button.classList.add('btn-warning');
    } else if (level === 3) {
        button.classList.add('btn-danger');
    }
}


function updateDataForPart(part) {
    let element = document.getElementById(part);
    if (!element) {
        console.error(`Element with ID '${part}' not found.`);
        return;
    }

    let currentLevel = parseInt(element.value) || 0;
    currentLevel = (currentLevel + 1) % 4;
    element.value = currentLevel;
    generateLampInput(part, currentLevel)
}


const orderedKeys = [
    { name: "Capot", coords: "184,137,221,126,262,124,304,125,329,130,350,134,365,139,372,171,376,259,374,269,334,250,272,244,217,246,170,270,170,198,173,155,174,142" },
    { name: "Pare-brise avant", coords: "372,267,359,331,352,351,301,347,240,347,190,351,181,313,170,272,208,249,281,245,335,251" },
    { name: "Aile avant droit", coords: "495,177,496,130,487,119,471,118,449,118,447,146,428,154,407,265,406,278,414,291,439,288,455,290,484,292,496,295,493,270,475,273,455,261,436,233,437,211,445,195,462,182,475,178" },
    { name: "Porte avant droite", coords: "495,295,409,293,373,348,361,377,354,410,352,431,429,428,486,425" },
    { name: "Porte arriere droite", coords: "487,427,411,426,356,432,348,439,348,536,419,555,435,549,468,523,487,516" },
    { name: "Aile arriere droit", coords: "495,521,452,533,431,548,413,550,400,554,359,538,349,552,357,565,374,599,395,635,397,647,403,663,426,664,427,683,438,680,441,661,441,624,440,596,438,578,438,555,447,539" },
    { name: "Feux avant droit", coords: "371,100,350,101,325,100,320,104,327,123,336,124,368,124,375,120,375,105" },
    { name: "Feux avant gauche", coords: "218,116,223,102,206,101,182,102,166,104,168,122,175,124,191,125,202,124,215,124" },
    { name: "Pare-choc", coords: "312,85,165,84,164,58,373,57,377,78,383,101,317,99,325,123,213,123,226,103,159,104,164,82,231,87,233,99,310,100" },
    { name: "Porte arriere gauche", coords: "105,425,52,430,49,520,90,530,116,555,150,553,178,544,196,534,198,473,198,436,162,434" },
    { name: "Aile arriere gauche", coords: "98,542,108,558,105,581,99,596,100,612,102,684,111,682,119,662,136,661,143,661,190,569,193,547,188,534,161,550,134,556,118,559" },
    { name: "Porte avant gauche", coords: "195,431,46,426,45,295,143,289,164,327,182,358" },
    { name: "Aile avant gauche", coords: "90,117,98,147,112,153,139,288,45,292,44,277,61,271,88,262,102,244,108,222,103,208,95,199,84,191,67,179,48,178,44,164,47,143,50,125" },
    { name: "Pare-choc arriere", coords: "164,733,378,737,381,750,371,779,308,773,203,774,170,779,160,753" },
    { name: "Feux arriere droit", coords: "352,687,339,732,375,733,373,687" },
    { name: "Feux arriere gauche", coords: "183,684,206,732,167,733,170,686" },
    { name: "Pare-brise arriere", coords: "347,562,356,646,337,658,279,666,225,662,187,652,184,623,188,591,194,569,194,562,233,568,278,570" },
    { name: "Plaque d\'immat arriere", coords: "242,699,284,699,306,700,309,718,256,718,236,713,234,704" },
    { name: "Plaque d\'immat avant", coords: "306,85,234,84,236,98,305,97" },
    { name: "Malle", coords: "355,654,236,669,188,649,185,686,202,724,212,729,238,729,253,732,338,729,357,655,316,687,312,718,234,716,234,698,310,700" },


];


function createImageMap() {

    const image = document.getElementById('carImage');
    if (!image) {
        console.error("Image element not found in the DOM");
        return;
    }

    const map = document.createElement('map');
    map.name = "carMap";
    image.useMap = "#carMap";

    orderedKeys.forEach(item => {
        const area = document.createElement('area');
        area.shape = 'poly';
        area.coords = item.coords;
        area.alt = item.name;
        area.href = "#";
        area.dataset.key = cleanKeyForId(item.name);
        area.className = 'zone-level-0';
        area.addEventListener('mouseenter', function() {
            this.classList.add('area-hover');
        });
        area.addEventListener('mouseleave', function() {
            this.classList.remove('area-hover');
        });

        area.addEventListener('click', function(event) {
            event.preventDefault();
            const part = this.dataset.key;
            console.log( "part", part);
            const input = document.querySelector(`input[name="${part}"]`);
            const currentLevel = parseInt(input.value) || 0;
            const newLevel = (currentLevel + 1) % 4;
            const initialLevel = document.querySelector(`input[name="${part}"]`).value || 0;

            console.log("Area clicked", this.dataset.key, "part", part, "newLevel", newLevel);

            // Update the input value
            input.value = newLevel;

            refreshLampDisplay(part,newLevel)
        });


        map.appendChild(area);
    });

    image.parentNode.insertBefore(map, image.nextSibling);
}
function createImageMap0() {
    const svgNS = "http://www.w3.org/2000/svg";
    const container = document.getElementById('carImage');
    if (!container) {
        console.error("Container element not found in the DOM");
        return;
    }

    container.innerHTML = '';

    // Create the SVG element
    const svg = document.createElementNS(svgNS, "svg");
    svg.setAttribute("viewBox", "0 0 800 600");
    svg.setAttribute("class", "svg-content");

    // Create shapes based on orderedKeys
    orderedKeys.forEach(item => {
        const shape = document.createElementNS(svgNS, "polygon"); // Use 'circle' or 'rect' as needed
        shape.setAttribute("points", item.coords);
        shape.setAttribute("fill", "#b3d9ff");
        shape.setAttribute("data-key", cleanKeyForId(item.name));
        shape.setAttribute("class", "interactive-area");

        // Add event listeners for interaction
        shape.addEventListener('click', function(event) {
            const part = this.getAttribute('data-key');
            const input = document.querySelector(`input[name="${part}"]`);
            const currentLevel = parseInt(input.value) || 0;
            const newLevel = (currentLevel + 1) % 4;
            input.value = newLevel;
            refreshLampDisplay(part, newLevel);
            console.log("Shape clicked", part, "newLevel", newLevel);
        });

        svg.appendChild(shape);
    });

    // Append the SVG to the container
    container.appendChild(svg);
}

function refreshSVGArea(key,value) {
    const svgArea = $(`[data-key="${key}"]`);

        if (svgArea.length) {
            svgArea.removeClass('zone-level-0 zone-level-1 zone-level-2 zone-level-3')
                   .addClass(`zone-level-${value}`);

            // Vous pouvez également manipuler directement le style
            switch(value) {
                case 0:
                    console.log(`SVG area found for key: ${svgArea}, attempting to update class to level ${value}`);
                    svgArea.css('fill', '#7ab8ee'); // Bleu
                    break;
                case 1:
                    console.log(`SVG area found for key: ${svgArea}, attempting to update class to level ${value}`);
                    svgArea.css('fill', '#76D7C4'); // Vert
                    break;
                case 2:
                    console.log(`SVG area found for key: ${svgArea}, attempting to update class to level ${value}`);
                    svgArea.css('fill', '#F8C471'); // Orange
                    break;
                case 3:
                    console.log(`SVG area found for key: ${svgArea}, attempting to update class to level ${value}`);
                    svgArea.css('fill', '#E74C3C'); // Rouge
                    break;
                default:
                    console.log(`SVG area found for key: ${svgArea}, attempting to update class to level ${value}`);
                    svgArea.css('fill', '#b3d9ff'); // Défaut
                    break;
            }
        }
}
function refreshLampDisplay(key, value) {
    const lampHTML = generateLampInput(key, value);
    const existingContainer = document.querySelector(`.lamp-container[data-key="${key}"]`);
    if (existingContainer) {
        // Remplacer directement le HTML du conteneur existant
        existingContainer.innerHTML = lampHTML;
        // Rattache le conteneur avec les lampes
        const newLampsContainer = existingContainer.querySelector('.lamp-container');
        existingContainer.replaceWith(newLampsContainer);
    }
    refreshSVGArea(key, value)

    }




function generateLampInput(key, value) {
    console.log('Generating lamps for', key, 'with value', value);
    let lamps = '';
    let hideClass = (key !== 'Rejet' && key !== 'carOrNot') ? 'hidden' : '';  // Applique la classe 'hidden' si ce n'est ni 'Rejet' ni 'carOrNot'

    // Générer les lampes seulement si la clé est 'Rejet' ou 'carOrNot'
    if (key === 'Rejet' || key === 'carOrNot') {
        for (let i = 1; i <= 3; i++) {
            const activeClass = value === i ? `level-${i} active` : '';
            lamps += `<div class="lamp ${activeClass}" data-level="${i}" onclick="lampClicked('${key}', ${i})">${i}</div>`;
        }
    }

    // Retourne le bloc HTML pour les lampes et le label, potentiellement masqué
    return `
        <div class="col-md-3 mb-3 ${hideClass}">
            <label class="form-label label-blue key-label">${key}</label>
            <div class="lamp-container" data-key="${key}">${lamps}</div>
            <input type="hidden" name="${key}" value="${value}">
        </div>
    `;
}

function lampClicked(key, level) {
    const input = document.querySelector(`input[name="${key}"]`);
    const currentLevel = parseInt(input.value);
    const newLevel = currentLevel === level ? 0 : level;
    input.value = newLevel;
    refreshLampDisplay(key, newLevel);
}

document.addEventListener('DOMContentLoaded', () => {
    document.body.addEventListener('click', function(event) {
        const lamp = event.target;
        if (lamp.classList.contains('lamp')) {
            const container = lamp.closest('.lamp-container');
            const key = container.dataset.key;
            const level = parseInt(lamp.dataset.level);
            const input = document.querySelector(`input[name="${key}"]`);
            const currentLevel = parseInt(input.value) || 0;

            if (currentLevel !== level) {
                Array.from(container.children).forEach(l => l.classList.remove('active', 'level-1', 'level-2', 'level-3'));
                lamp.classList.add('active', `level-${level}`);
                input.value = level;
            } else {
                lamp.classList.remove('active', `level-${level}`);
                input.value = 0;
            }


            console.log(`Lamp for ${key} set to level ${input.value}`);
            refreshLampDisplay(key, level)
        }
    });
});


function createElements() {
    const container = document.getElementById('dataDisplay');
    if (!container) {
        console.error("Data display container not found in the DOM");
        return;
    }

    orderedKeys.forEach(item => {
        const elementId = cleanKeyForId(item.name);
        const div = document.createElement('div');
        div.id = elementId;
        div.textContent = item.name;
        div.style.position = "absolute";
        div.style.left = `${item.left}px`;
        div.style.top = `${item.top}px`;
        div.style.color = "white";

        container.appendChild(div);
    });
}


document.addEventListener('DOMContentLoaded', function() {
    createImageMap();
    createImageMap0();
    attachEventListeners();
});

document.querySelectorAll('area').forEach(area => {
    area.addEventListener('mouseenter', function() {
        const coords = this.coords.split(',').map(x => parseInt(x));
        const overlay = document.createElement('div');
        overlay.style.position = 'absolute';
        overlay.style.left = `${coords[0]}px`;
        overlay.style.top = `${coords[1]}px`;
        overlay.style.width = `${coords[2] - coords[0]}px`;
        overlay.style.height = `${coords[3] - coords[1]}px`;
        overlay.style.backgroundColor = 'rgba(255, 255, 255, 0.5)';
        overlay.style.outline = '2px solid black';
        document.body.appendChild(overlay);
        this.overlay = overlay;
    });


});

document.querySelectorAll('.interactive-area').forEach(area => {
    area.addEventListener('click', function() {
        const key = this.getAttribute('data-key');
        toggleAreaColor(this);
        console.log(`Area ${key} clicked.`);
    });
});

function toggleAreaColor(element) {
    const isActive = element.getAttribute('data-active') === 'true';
    if (isActive) {
        element.setAttribute('fill', '#b3d9ff'); // Default color
        element.setAttribute('data-active', 'false');
    } else {
        element.setAttribute('fill', '#ff6666'); // Active color
        element.setAttribute('data-active', 'true');
    }
}

function validateAsNotACar() {
    const dataDisplay = document.getElementById('dataDisplay');
    const imageName = dataDisplay.getAttribute('data-imageName');
    const validatorName = document.getElementById('validatorName').value.toUpperCase();

    if (!imageName) {
        console.error('Image name is missing!');
        alert('Image name is missing!');
        return;
    }

    if (!validatorName) {
        alert('Validator name is required!');
        return;
    }

    const newData = {
        validatorName: validatorName,
        "Aile avant droit": "0",
        "Porte avant droite": "0",
        "Porte arriere droite": "0",
        "Aile arriere droit": "0",
        "Aile arriere gauche": "0",
        "Aile avant gauche": "0",
        "Capot": "0",
        "Feux arriere droit": "0",
        "Feux arriere gauche": "0",
        "Feux avant droit": "0",
        "Feux avant gauche": "0",
        "Malle": "0",
        "Pare-brise arriere": "0",
        "Pare-brise avant": "0",
        "Pare-choc": "0",
        "Pare-choc arriere": "0",
        "Plaque d'immat arriere": "0",
        "Plaque d'immat avant": "0",
        "Porte arriere droite": "0",
        "Porte arriere gauche": "0",
        "Porte avant droite": "0",
        "Porte avant gauche": "0",
        "Rejet": "1",
        "carOrNot": "0"
    };

    // Appeler l'API pour mettre à jour les données
    const updateUrl = `${apiBaseUrl}/updateImageIn${isPendingMode ? 'Pending' : 'Initial'}`;
    axios.post(updateUrl, { imageName: imageName, newData: newData })
        .then(response => {
            showToast('Data Updated as Not a Car and Moved to Next!');
            incrementValidatorCount(validatorName)
            moveToNextState(() => {
                console.log('Moved to next after marking as not a car.');
            });
        })
        .catch(error => {
            console.error('Error updating data:', error);
            alert('Failed to update data. Please try again!');
        });
}
function ResetData() {
    const dataDisplay = document.getElementById('dataDisplay');
    const validatorName = document.getElementById('validatorName').value.toUpperCase();

    const newData = {

        "Aile avant droit": "0", "Porte avant droite": "0", "Porte arriere droite": "0", "Aile arriere droit": "0",
        "Aile arriere gauche": "0", "Aile avant gauche": "0", "Capot": "0", "Feux arriere droit": "0",
        "Feux arriere gauche": "0", "Feux avant droit": "0", "Feux avant gauche": "0", "Malle": "0",
        "Pare-brise arriere": "0", "Pare-brise avant": "0", "Pare-choc": "0", "Pare-choc arriere": "0",
        "Plaque d'immat arriere": "0", "Plaque d'immat avant": "0", "Porte arriere droite": "0",
        "Porte arriere gauche": "0", "Porte avant droite": "0", "Porte avant gauche": "0", "Rejet": "0",
        "carOrNot": "1"
    };

    Object.keys(newData).forEach(key => {
        lampClicked(key, 0)
        const inputElement = document.querySelector(`input[name="${key}"]`);
        if (inputElement) {
            inputElement.value = newData[key];
        }
        const lamps = document.querySelectorAll(`.lamp-container[data-part="${key}"] .lamp`);
        lamps.forEach(lamp => {
            const level = parseInt(lamp.textContent);
            if (level === parseInt(newData[key])) {
                lamp.classList.add('active');
            } else {
                lamp.classList.remove('active');
            }
        });
    });
    updateButtonColors(newData);
    console.log("All data fields have been reset.");
}