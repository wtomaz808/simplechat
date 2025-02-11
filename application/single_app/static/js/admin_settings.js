// js/admin_settings.js

// Use the already-defined window.* vars (if they exist) or default to empty arrays
let gptSelected = window.gptSelected || [];
let gptAll      = window.gptAll || [];

let embeddingSelected = window.embeddingSelected || [];
let embeddingAll      = window.embeddingAll || [];

let imageSelected = window.imageSelected || [];
let imageAll      = window.imageAll || [];

document.addEventListener('DOMContentLoaded', () => {
    // Render any models we already have in memory
    renderGPTModels();
    renderEmbeddingModels();
    renderImageModels();

    // Update hidden inputs right away so if user saves without refetching,
    // the “selected/all” data is correctly submitted
    updateGptHiddenInput();
    updateEmbeddingHiddenInput();
    updateImageHiddenInput();

    // Add event listeners for toggles and test buttons
    setupToggles();
    setupTestButtons();
});

////////////////////////////////////////////////////////////////////////////
// MODEL RENDERING
////////////////////////////////////////////////////////////////////////////
function renderGPTModels() {
    const listDiv = document.getElementById('gpt_models_list');
    if (!gptAll || gptAll.length === 0) {
        listDiv.innerHTML = '<p class="text-warning">No GPT models found. Click "Fetch GPT Models" to populate.</p>';
        return;
    }

    let html = '<ul class="list-group">';
    gptAll.forEach(m => {
        const isSelected = gptSelected.some(sel =>
            sel.deploymentName === m.deploymentName &&
            sel.modelName === m.modelName
        );
        const buttonLabel = isSelected ? 'Selected' : 'Select';
        const buttonDisabled = isSelected ? 'disabled' : '';
        html += `
            <li class="list-group-item d-flex justify-content-between align-items-center">
                <span>${m.deploymentName} (Model: ${m.modelName})</span>
                <button class="btn btn-sm btn-primary" ${buttonDisabled}
                    onclick="selectGptModel('${m.deploymentName}', '${m.modelName}')">
                    ${buttonLabel}
                </button>
            </li>
        `;
    });
    html += '</ul>';
    listDiv.innerHTML = html;
}

function renderEmbeddingModels() {
    const listDiv = document.getElementById('embedding_models_list');
    if (!embeddingAll || embeddingAll.length === 0) {
        listDiv.innerHTML = '<p class="text-warning">No embedding models found. Click "Fetch Embedding Models" to populate.</p>';
        return;
    }

    let html = '<ul class="list-group">';
    embeddingAll.forEach(m => {
        const isSelected = embeddingSelected.some(sel =>
            sel.deploymentName === m.deploymentName &&
            sel.modelName === m.modelName
        );
        const buttonLabel = isSelected ? 'Selected' : 'Select';
        const buttonDisabled = isSelected ? 'disabled' : '';
        html += `
            <li class="list-group-item d-flex justify-content-between align-items-center">
                <span>${m.deploymentName} (Model: ${m.modelName})</span>
                <button class="btn btn-sm btn-primary" ${buttonDisabled}
                    onclick="selectEmbeddingModel('${m.deploymentName}', '${m.modelName}')">
                    ${buttonLabel}
                </button>
            </li>
        `;
    });
    html += '</ul>';
    listDiv.innerHTML = html;
}

function renderImageModels() {
    const listDiv = document.getElementById('image_models_list');
    if (!imageAll || imageAll.length === 0) {
        listDiv.innerHTML = '<p class="text-warning">No image models found. Click "Fetch Image Models" to populate.</p>';
        return;
    }

    let html = '<ul class="list-group">';
    imageAll.forEach(m => {
        const isSelected = imageSelected.some(sel =>
            sel.deploymentName === m.deploymentName &&
            sel.modelName === m.modelName
        );
        const buttonLabel = isSelected ? 'Selected' : 'Select';
        const buttonDisabled = isSelected ? 'disabled' : '';
        html += `
            <li class="list-group-item d-flex justify-content-between align-items-center">
                <span>${m.deploymentName} (Model: ${m.modelName})</span>
                <button class="btn btn-sm btn-primary" ${buttonDisabled}
                    onclick="selectImageModel('${m.deploymentName}', '${m.modelName}')">
                    ${buttonLabel}
                </button>
            </li>
        `;
    });
    html += '</ul>';
    listDiv.innerHTML = html;
}

////////////////////////////////////////////////////////////////////////////
// GPT: FETCH & SELECT
////////////////////////////////////////////////////////////////////////////
document.getElementById('fetch_gpt_models_btn').addEventListener('click', async () => {
    const listDiv = document.getElementById('gpt_models_list');
    listDiv.innerHTML = 'Fetching...';
    try {
        const resp = await fetch('/api/models/gpt');
        const data = await resp.json();
        if (resp.ok && data.models && data.models.length > 0) {
            gptAll = data.models;
            renderGPTModels();
            updateGptHiddenInput();
        } else {
            listDiv.innerHTML = `<p class="text-danger">Error: ${data.error || 'No GPT models found'}</p>`;
        }
    } catch (err) {
        listDiv.innerHTML = `<p class="text-danger">Error fetching GPT models: ${err.message}</p>`;
    }
});

window.selectGptModel = (deploymentName, modelName) => {
    // Always store just one selected GPT model
    gptSelected = [{ deploymentName, modelName }];
    renderGPTModels();
    updateGptHiddenInput();
    alert(`Selected GPT model: ${deploymentName}`);
};

function updateGptHiddenInput() {
    const payload = {
        selected: gptSelected,
        all: gptAll
    };
    document.getElementById('gpt_model_json').value = JSON.stringify(payload);
}

////////////////////////////////////////////////////////////////////////////
// EMBEDDINGS: FETCH & SELECT
////////////////////////////////////////////////////////////////////////////
document.getElementById('fetch_embedding_models_btn').addEventListener('click', async () => {
    const listDiv = document.getElementById('embedding_models_list');
    listDiv.innerHTML = 'Fetching...';
    try {
        const resp = await fetch('/api/models/embedding');
        const data = await resp.json();
        if (resp.ok && data.models && data.models.length > 0) {
            embeddingAll = data.models;
            renderEmbeddingModels();
            updateEmbeddingHiddenInput();
        } else {
            listDiv.innerHTML = `<p class="text-danger">Error: ${data.error || 'No embedding models found'}</p>`;
        }
    } catch (err) {
        listDiv.innerHTML = `<p class="text-danger">Error fetching embedding models: ${err.message}</p>`;
    }
});

window.selectEmbeddingModel = (deploymentName, modelName) => {
    embeddingSelected = [{ deploymentName, modelName }];
    renderEmbeddingModels();
    updateEmbeddingHiddenInput();
    alert(`Selected embedding model: ${deploymentName}`);
};

function updateEmbeddingHiddenInput() {
    const payload = {
        selected: embeddingSelected,
        all: embeddingAll
    };
    document.getElementById('embedding_model_json').value = JSON.stringify(payload);
}

////////////////////////////////////////////////////////////////////////////
// IMAGE GEN: FETCH & SELECT
////////////////////////////////////////////////////////////////////////////
document.getElementById('fetch_image_models_btn').addEventListener('click', async () => {
    const listDiv = document.getElementById('image_models_list');
    listDiv.innerHTML = 'Fetching...';
    try {
        const resp = await fetch('/api/models/image');
        const data = await resp.json();
        if (resp.ok && data.models && data.models.length > 0) {
            imageAll = data.models;
            renderImageModels();
            updateImageHiddenInput();
        } else {
            listDiv.innerHTML = `<p class="text-danger">Error: ${data.error || 'No image models found'}</p>`;
        }
    } catch (err) {
        listDiv.innerHTML = `<p class="text-danger">Error fetching image models: ${err.message}</p>`;
    }
});

window.selectImageModel = (deploymentName, modelName) => {
    imageSelected = [{ deploymentName, modelName }];
    renderImageModels();
    updateImageHiddenInput();
    alert(`Selected image model: ${deploymentName}`);
};

function updateImageHiddenInput() {
    const payload = {
        selected: imageSelected,
        all: imageAll
    };
    document.getElementById('image_gen_model_json').value = JSON.stringify(payload);
}

////////////////////////////////////////////////////////////////////////////
// TOGGLES & COLLAPSING FIELDS
////////////////////////////////////////////////////////////////////////////
function setupToggles() {
    // GPT: APIM vs. non-APIM
    const enableGptApim = document.getElementById('enable_gpt_apim');
    enableGptApim.addEventListener('change', function () {
        document.getElementById('non_apim_gpt_settings').style.display = this.checked ? 'none' : 'block';
        document.getElementById('apim_gpt_settings').style.display = this.checked ? 'block' : 'none';
    });

    // Embeddings: APIM vs. non-APIM
    const enableEmbeddingApim = document.getElementById('enable_embedding_apim');
    enableEmbeddingApim.addEventListener('change', function () {
        document.getElementById('non_apim_embedding_settings').style.display = this.checked ? 'none' : 'block';
        document.getElementById('apim_embedding_settings').style.display = this.checked ? 'block' : 'none';
    });

    // Image Generation: main toggle
    const enableImageGen = document.getElementById('enable_image_generation');
    enableImageGen.addEventListener('change', function () {
        document.getElementById('image_gen_settings').style.display = this.checked ? 'block' : 'none';
    });

    // Image Generation: APIM vs. non-APIM
    const enableImageGenApim = document.getElementById('enable_image_gen_apim');
    enableImageGenApim.addEventListener('change', function () {
        document.getElementById('non_apim_image_gen_settings').style.display = this.checked ? 'none' : 'block';
        document.getElementById('apim_image_gen_settings').style.display = this.checked ? 'block' : 'none';
    });

    // Web Search
    const enableWebSearch = document.getElementById('enable_web_search');
    enableWebSearch.addEventListener('change', function () {
        document.getElementById('web_search_settings').style.display = this.checked ? 'block' : 'none';
    });

    // External APIs
    const useExternalApis = document.getElementById('use_external_apis');
    useExternalApis.addEventListener('change', function () {
        document.getElementById('external_apis_settings').style.display = this.checked ? 'block' : 'none';
    });

    // GPT Auth Type
    document.getElementById('azure_openai_gpt_authentication_type')
        .addEventListener('change', function () {
            document.getElementById('gpt_key_container').style.display =
                (this.value === 'key') ? 'block' : 'none';
        });

    // Embeddings Auth Type
    document.getElementById('azure_openai_embedding_authentication_type')
        .addEventListener('change', function () {
            document.getElementById('embedding_key_container').style.display =
                (this.value === 'key') ? 'block' : 'none';
        });

    // Image Auth Type
    document.getElementById('azure_openai_image_gen_authentication_type')
        .addEventListener('change', function () {
            document.getElementById('image_gen_key_container').style.display =
                (this.value === 'key') ? 'block' : 'none';
        });
}

////////////////////////////////////////////////////////////////////////////
// TEST BUTTONS
////////////////////////////////////////////////////////////////////////////
function setupTestButtons() {
    // GPT
    document.getElementById('test_gpt_button').addEventListener('click', async () => {
        const resultDiv = document.getElementById('test_gpt_result');
        resultDiv.innerHTML = 'Testing GPT...';
        try {
            // Placeholder fetch – update with your actual test endpoint
            const resp = await fetch('/api/test/gpt');
            const data = await resp.json();
            if (resp.ok) {
                resultDiv.innerHTML = `<span class="text-success">Success: ${data.message}</span>`;
            } else {
                resultDiv.innerHTML = `<span class="text-danger">Error: ${data.error || 'Unknown error'}</span>`;
            }
        } catch (err) {
            resultDiv.innerHTML = `<span class="text-danger">Error: ${err.message}</span>`;
        }
    });

    // Embeddings
    document.getElementById('test_embedding_button').addEventListener('click', async () => {
        const resultDiv = document.getElementById('test_embedding_result');
        resultDiv.innerHTML = 'Testing Embeddings...';
        try {
            // Placeholder fetch – update with your actual test endpoint
            const resp = await fetch('/api/test/embedding');
            const data = await resp.json();
            if (resp.ok) {
                resultDiv.innerHTML = `<span class="text-success">Success: ${data.message}</span>`;
            } else {
                resultDiv.innerHTML = `<span class="text-danger">Error: ${data.error || 'Unknown error'}</span>`;
            }
        } catch (err) {
            resultDiv.innerHTML = `<span class="text-danger">Error: ${err.message}</span>`;
        }
    });

    // Image
    document.getElementById('test_image_button').addEventListener('click', async () => {
        const resultDiv = document.getElementById('test_image_result');
        resultDiv.innerHTML = 'Testing Image Generation...';
        try {
            // Placeholder fetch – update with your actual test endpoint
            const resp = await fetch('/api/test/image');
            const data = await resp.json();
            if (resp.ok) {
                resultDiv.innerHTML = `<span class="text-success">Success: ${data.message}</span>`;
            } else {
                resultDiv.innerHTML = `<span class="text-danger">Error: ${data.error || 'Unknown error'}</span>`;
            }
        } catch (err) {
            resultDiv.innerHTML = `<span class="text-danger">Error: ${err.message}</span>`;
        }
    });

    // External APIs
    document.getElementById('test_connection_button').addEventListener('click', async () => {
        const resultDiv = document.getElementById('test_connection_result');
        resultDiv.innerHTML = 'Testing External APIs...';
        try {
            // Placeholder fetch – update with your actual test endpoint
            const resp = await fetch('/api/test/external');
            const data = await resp.json();
            if (resp.ok) {
                resultDiv.innerHTML = `<span class="text-success">Success: ${data.message}</span>`;
            } else {
                resultDiv.innerHTML = `<span class="text-danger">Error: ${data.error || 'Unknown error'}</span>`;
            }
        } catch (err) {
            resultDiv.innerHTML = `<span class="text-danger">Error: ${err.message}</span>`;
        }
    });
}

////////////////////////////////////////////////////////////////////////////
// SHOW/HIDE PASSWORD FIELDS
////////////////////////////////////////////////////////////////////////////
document.getElementById('toggle_gpt_key').addEventListener('click', function () {
    const inp = document.getElementById('azure_openai_gpt_key');
    if (inp.type === 'password') {
        inp.type = 'text';
        this.textContent = 'Hide';
    } else {
        inp.type = 'password';
        this.textContent = 'Show';
    }
});

document.getElementById('toggle_embedding_key').addEventListener('click', function () {
    const inp = document.getElementById('azure_openai_embedding_key');
    if (inp.type === 'password') {
        inp.type = 'text';
        this.textContent = 'Hide';
    } else {
        inp.type = 'password';
        this.textContent = 'Show';
    }
});

document.getElementById('toggle_image_gen_key').addEventListener('click', function () {
    const inp = document.getElementById('azure_openai_image_gen_key');
    if (inp.type === 'password') {
        inp.type = 'text';
        this.textContent = 'Hide';
    } else {
        inp.type = 'password';
        this.textContent = 'Show';
    }
});

document.getElementById('toggle_bing_search_key').addEventListener('click', function () {
    const inp = document.getElementById('bing_search_key');
    if (inp.type === 'password') {
        inp.type = 'text';
        this.textContent = 'Hide';
    } else {
        inp.type = 'password';
        this.textContent = 'Show';
    }
});

document.getElementById('toggle_search_key').addEventListener('click', function () {
    const inp = document.getElementById('azure_ai_search_key');
    if (inp.type === 'password') {
        inp.type = 'text';
        this.textContent = 'Hide';
    } else {
        inp.type = 'password';
        this.textContent = 'Show';
    }
});

document.getElementById('toggle_docintel_key').addEventListener('click', function () {
    const inp = document.getElementById('azure_document_intelligence_key');
    if (inp.type === 'password') {
        inp.type = 'text';
        this.textContent = 'Hide';
    } else {
        inp.type = 'password';
        this.textContent = 'Show';
    }
});

// APIM subscription key toggles:
document.getElementById('toggle_azure_apim_gpt_subscription_key').addEventListener('click', function () {
    const inp = document.getElementById('azure_apim_gpt_subscription_key');
    if (inp.type === 'password') {
        inp.type = 'text';
        this.textContent = 'Hide';
    } else {
        inp.type = 'password';
        this.textContent = 'Show';
    }
});

document.getElementById('toggle_azure_apim_embedding_subscription_key').addEventListener('click', function () {
    const inp = document.getElementById('azure_apim_embedding_subscription_key');
    if (inp.type === 'password') {
        inp.type = 'text';
        this.textContent = 'Hide';
    } else {
        inp.type = 'password';
        this.textContent = 'Show';
    }
});

document.getElementById('toggle_azure_apim_image_gen_subscription_key').addEventListener('click', function () {
    const inp = document.getElementById('azure_apim_image_gen_subscription_key');
    if (inp.type === 'password') {
        inp.type = 'text';
        this.textContent = 'Hide';
    } else {
        inp.type = 'password';
        this.textContent = 'Show';
    }
});
