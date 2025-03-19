// admin_settings.js

let gptSelected = window.gptSelected || [];
let gptAll      = window.gptAll || [];

let embeddingSelected = window.embeddingSelected || [];
let embeddingAll      = window.embeddingAll || [];

let imageSelected = window.imageSelected || [];
let imageAll      = window.imageAll || [];

document.addEventListener('DOMContentLoaded', () => {
    renderGPTModels();
    renderEmbeddingModels();
    renderImageModels();

    updateGptHiddenInput();
    updateEmbeddingHiddenInput();
    updateImageHiddenInput();

    setupToggles();

    setupTestButtons();

    function activateTabFromHash() {
        const hash = window.location.hash;
        if (hash) {
            const tabButton = document.querySelector(`button.nav-link[data-bs-target="${hash}"]`);
            if (tabButton) {
                const tab = new bootstrap.Tab(tabButton);
                tab.show();
            }
        }
    }

    activateTabFromHash();

    document.querySelectorAll('.nav-link').forEach(tab => {
        tab.addEventListener('click', function () {
            history.pushState(null, null, this.getAttribute('data-bs-target'));
        });
    });

    window.addEventListener("popstate", activateTabFromHash);

});

function renderGPTModels() {
    const listDiv = document.getElementById('gpt_models_list');
    if (!listDiv) return;

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
    if (!listDiv) return;

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
    if (!listDiv) return;

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

const fetchGptBtn = document.getElementById('fetch_gpt_models_btn');
if (fetchGptBtn) {
    fetchGptBtn.addEventListener('click', async () => {
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
}

window.selectGptModel = (deploymentName, modelName) => {
    // Always store just one selected GPT model
    gptSelected = [{ deploymentName, modelName }];
    renderGPTModels();
    updateGptHiddenInput();
    alert(`Selected GPT model: ${deploymentName}`);
};

function updateGptHiddenInput() {
    const gptInput = document.getElementById('gpt_model_json');
    if (!gptInput) return;
    const payload = {
        selected: gptSelected,
        all: gptAll
    };
    gptInput.value = JSON.stringify(payload);
}

const fetchEmbeddingBtn = document.getElementById('fetch_embedding_models_btn');
if (fetchEmbeddingBtn) {
    fetchEmbeddingBtn.addEventListener('click', async () => {
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
}

window.selectEmbeddingModel = (deploymentName, modelName) => {
    embeddingSelected = [{ deploymentName, modelName }];
    renderEmbeddingModels();
    updateEmbeddingHiddenInput();
    alert(`Selected embedding model: ${deploymentName}`);
};

function updateEmbeddingHiddenInput() {
    const embInput = document.getElementById('embedding_model_json');
    if (!embInput) return;
    const payload = {
        selected: embeddingSelected,
        all: embeddingAll
    };
    embInput.value = JSON.stringify(payload);
}

const fetchImageBtn = document.getElementById('fetch_image_models_btn');
if (fetchImageBtn) {
    fetchImageBtn.addEventListener('click', async () => {
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
}

window.selectImageModel = (deploymentName, modelName) => {
    imageSelected = [{ deploymentName, modelName }];
    renderImageModels();
    updateImageHiddenInput();
    alert(`Selected image model: ${deploymentName}`);
};

function updateImageHiddenInput() {
    const imgInput = document.getElementById('image_gen_model_json');
    if (!imgInput) return;
    const payload = {
        selected: imageSelected,
        all: imageAll
    };
    imgInput.value = JSON.stringify(payload);
}


function setupToggles() {
    const enableGptApim = document.getElementById('enable_gpt_apim');
    if (enableGptApim) {
        enableGptApim.addEventListener('change', function () {
            document.getElementById('non_apim_gpt_settings').style.display = this.checked ? 'none' : 'block';
            document.getElementById('apim_gpt_settings').style.display = this.checked ? 'block' : 'none';
        });
    }

    const enableEmbeddingApim = document.getElementById('enable_embedding_apim');
    if (enableEmbeddingApim) {
        enableEmbeddingApim.addEventListener('change', function () {
            document.getElementById('non_apim_embedding_settings').style.display = this.checked ? 'none' : 'block';
            document.getElementById('apim_embedding_settings').style.display = this.checked ? 'block' : 'none';
        });
    }

    const enableImageGen = document.getElementById('enable_image_generation');
    if (enableImageGen) {
        enableImageGen.addEventListener('change', function () {
            document.getElementById('image_gen_settings').style.display = this.checked ? 'block' : 'none';
        });
    }

    const enableImageGenApim = document.getElementById('enable_image_gen_apim');
    if (enableImageGenApim) {
        enableImageGenApim.addEventListener('change', function () {
            document.getElementById('non_apim_image_gen_settings').style.display = this.checked ? 'none' : 'block';
            document.getElementById('apim_image_gen_settings').style.display = this.checked ? 'block' : 'none';
        });
    }

    const enableEnhancedCitation = document.getElementById('enable_enhanced_citations');
    if (enableEnhancedCitation) {
        toggleEnhancedCitation(enableEnhancedCitation.checked);
        enableEnhancedCitation.addEventListener('change', function(){
            toggleEnhancedCitation(this.checked);
        });
    }

    const enableContentSafetyCheckbox = document.getElementById('enable_content_safety');
    if (enableContentSafetyCheckbox) {
        enableContentSafetyCheckbox.addEventListener('change', function() {
            const safetySettings = document.getElementById('content_safety_settings');
            safetySettings.style.display = this.checked ? 'block' : 'none';
        });
    }

    const enableContentSafetyApim = document.getElementById('enable_content_safety_apim');
    if (enableContentSafetyApim) {
        enableContentSafetyApim.addEventListener('change', function() {
            document.getElementById('non_apim_content_safety_settings').style.display = this.checked ? 'none' : 'block';
            document.getElementById('apim_content_safety_settings').style.display = this.checked ? 'block' : 'none';
        });
    }

    const enableWebSearch = document.getElementById('enable_web_search');
    if (enableWebSearch) {
        enableWebSearch.addEventListener('change', function () {
            document.getElementById('web_search_settings').style.display = this.checked ? 'block' : 'none';
        });
    }

    const enableWebSearchApim = document.getElementById('enable_web_search_apim');
    if (enableWebSearchApim) {
        enableWebSearchApim.addEventListener('change', function () {
            document.getElementById('non_apim_web_search_settings').style.display = this.checked ? 'none' : 'block';
            document.getElementById('apim_web_search_settings').style.display = this.checked ? 'block' : 'none';
        });
    }

    const enableAiSearchApim = document.getElementById('enable_ai_search_apim');
    if (enableAiSearchApim) {
        enableAiSearchApim.addEventListener('change', function () {
            document.getElementById('non_apim_ai_search_settings').style.display = this.checked ? 'none' : 'block';
            document.getElementById('apim_ai_search_settings').style.display = this.checked ? 'block' : 'none';
        });
    }

    const enableDocumentIntelligenceApim = document.getElementById('enable_document_intelligence_apim');
    if (enableDocumentIntelligenceApim) {
        enableDocumentIntelligenceApim.addEventListener('change', function () {
            document.getElementById('non_apim_document_intelligence_settings').style.display = this.checked ? 'none' : 'block';
            document.getElementById('apim_document_intelligence_settings').style.display = this.checked ? 'block' : 'none';
        });
    }

    const gptAuthType = document.getElementById('azure_openai_gpt_authentication_type');
    if (gptAuthType) {
        gptAuthType.addEventListener('change', function () {
            document.getElementById('gpt_key_container').style.display =
                (this.value === 'key') ? 'block' : 'none';
        });
    }

    const embeddingAuthType = document.getElementById('azure_openai_embedding_authentication_type');
    if (embeddingAuthType) {
        embeddingAuthType.addEventListener('change', function () {
            document.getElementById('embedding_key_container').style.display =
                (this.value === 'key') ? 'block' : 'none';
        });
    }

    const imgAuthType = document.getElementById('azure_openai_image_gen_authentication_type');
    if (imgAuthType) {
        imgAuthType.addEventListener('change', function () {
            document.getElementById('image_gen_key_container').style.display =
                (this.value === 'key') ? 'block' : 'none';
        });
    }

    const contentSafetyAuthType = document.getElementById('content_safety_authentication_type');
    if (contentSafetyAuthType) {
        contentSafetyAuthType.addEventListener('change', function () {
            document.getElementById('content_safety_key_container').style.display =
                (this.value === 'key') ? 'block' : 'none';
        });
    }

    const aiSearchAuthType = document.getElementById('azure_ai_search_authentication_type');
    if (aiSearchAuthType) {
        aiSearchAuthType.addEventListener('change', function () {
            document.getElementById('azure_ai_search_key_container').style.display =
                (this.value === 'key') ? 'block' : 'none';
        });
    }

    const docIntelAuthType = document.getElementById('azure_document_intelligence_authentication_type');
    if (docIntelAuthType) {
        docIntelAuthType.addEventListener('change', function () {
            document.getElementById('azure_document_intelligence_key_container').style.display =
                (this.value === 'key') ? 'block' : 'none';
        });
    }

    const officeAuthType = document.getElementById('office_docs_authentication_type');
    if (officeAuthType) {
        officeAuthType.addEventListener('change', function(){
            document.getElementById('office_docs_key_container').style.display =
                (this.value === 'key') ? 'block' : 'none';
        });
    }

    const videoAuthType = document.getElementById('video_files_authentication_type');
    if (videoAuthType) {
        videoAuthType.addEventListener('change', function(){
            document.getElementById('video_files_key_container').style.display =
                (this.value === 'key') ? 'block' : 'none';
        });
    }

    const audioAuthType = document.getElementById('audio_files_authentication_type');
    if (audioAuthType) {
        audioAuthType.addEventListener('change', function(){
            document.getElementById('audio_files_key_container').style.display =
                (this.value === 'key') ? 'block' : 'none';
        });
    }
}

function setupTestButtons() {

    const testGptBtn = document.getElementById('test_gpt_button');
    if (testGptBtn) {
        testGptBtn.addEventListener('click', async () => {
            const resultDiv = document.getElementById('test_gpt_result');
            resultDiv.innerHTML = 'Testing GPT...';

            const enableApim = document.getElementById('enable_gpt_apim').checked;
            
            const payload = {
                test_type: 'gpt',
                enable_apim: enableApim,
                selected_model: gptSelected[0] || null
            };

            if (enableApim) {
                payload.apim = {
                    endpoint: document.getElementById('azure_apim_gpt_endpoint').value,
                    api_version: document.getElementById('azure_apim_gpt_api_version').value,
                    deployment: document.getElementById('azure_apim_gpt_deployment').value,
                    subscription_key: document.getElementById('azure_apim_gpt_subscription_key').value
                };
            } else {
                payload.direct = {
                    endpoint: document.getElementById('azure_openai_gpt_endpoint').value,
                    auth_type: document.getElementById('azure_openai_gpt_authentication_type').value,
                    subscription_id: document.getElementById('azure_openai_gpt_subscription_id').value,
                    resource_group: document.getElementById('azure_openai_gpt_resource_group').value,
                    key: document.getElementById('azure_openai_gpt_key').value,
                    api_version: document.getElementById('azure_openai_gpt_api_version').value
                };
            }

            try {
                const resp = await fetch('/api/admin/settings/test_connection', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await resp.json();
                if (resp.ok) {
                    resultDiv.innerHTML = `<span class="text-success">${data.message}</span>`;
                } else {
                    resultDiv.innerHTML = `<span class="text-danger">${data.error || 'Error testing GPT'}</span>`;
                }
            } catch (err) {
                resultDiv.innerHTML = `<span class="text-danger">Error: ${err.message}</span>`;
            }
        });
    }

    const testEmbeddingBtn = document.getElementById('test_embedding_button');
    if (testEmbeddingBtn) {
        testEmbeddingBtn.addEventListener('click', async () => {
            const resultDiv = document.getElementById('test_embedding_result');
            resultDiv.innerHTML = 'Testing Embeddings...';

            const enableApim = document.getElementById('enable_embedding_apim').checked;

            const payload = {
                test_type: 'embedding',
                enable_apim: enableApim,
                selected_model: embeddingSelected[0] || null
            };

            if (enableApim) {
                payload.apim = {
                    endpoint: document.getElementById('azure_apim_embedding_endpoint').value,
                    api_version: document.getElementById('azure_apim_embedding_api_version').value,
                    deployment: document.getElementById('azure_apim_embedding_deployment').value,
                    subscription_key: document.getElementById('azure_apim_embedding_subscription_key').value
                };
            } else {
                payload.direct = {
                    endpoint: document.getElementById('azure_openai_embedding_endpoint').value,
                    auth_type: document.getElementById('azure_openai_embedding_authentication_type').value,
                    subscription_id: document.getElementById('azure_openai_embedding_subscription_id').value,
                    resource_group: document.getElementById('azure_openai_embedding_resource_group').value,
                    key: document.getElementById('azure_openai_embedding_key').value,
                    api_version: document.getElementById('azure_openai_embedding_api_version').value                };
            }

            try {
                const resp = await fetch('/api/admin/settings/test_connection', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await resp.json();
                if (resp.ok) {
                    resultDiv.innerHTML = `<span class="text-success">${data.message}</span>`;
                } else {
                    resultDiv.innerHTML = `<span class="text-danger">${data.error || 'Error testing Embeddings'}</span>`;
                }
            } catch (err) {
                resultDiv.innerHTML = `<span class="text-danger">Error: ${err.message}</span>`;
            }
        });
    }

    const testImageBtn = document.getElementById('test_image_button');
    if (testImageBtn) {
        testImageBtn.addEventListener('click', async () => {
            const resultDiv = document.getElementById('test_image_result');
            resultDiv.innerHTML = 'Testing Image Generation...';

            const enableApim = document.getElementById('enable_image_gen_apim').checked;

            const payload = {
                test_type: 'image',
                enable_apim: enableApim,
                selected_model: imageSelected[0] || null
            };

            if (enableApim) {
                payload.apim = {
                    endpoint: document.getElementById('azure_apim_image_gen_endpoint').value,
                    api_version: document.getElementById('azure_apim_image_gen_api_version').value,
                    deployment: document.getElementById('azure_apim_image_gen_deployment').value,
                    subscription_key: document.getElementById('azure_apim_image_gen_subscription_key').value
                };
            } else {
                payload.direct = {
                    endpoint: document.getElementById('azure_openai_image_gen_endpoint').value,
                    auth_type: document.getElementById('azure_openai_image_gen_authentication_type').value,
                    subscription_id: document.getElementById('azure_openai_image_gen_subscription_id').value,
                    resource_group: document.getElementById('azure_openai_image_gen_resource_group').value,
                    key: document.getElementById('azure_openai_image_gen_key').value,
                    api_version: document.getElementById('azure_openai_image_gen_api_version').value
                };
            }

            try {
                const resp = await fetch('/api/admin/settings/test_connection', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await resp.json();
                if (resp.ok) {
                    resultDiv.innerHTML = `<span class="text-success">${data.message}</span>`;
                } else {
                    resultDiv.innerHTML = `<span class="text-danger">${data.error || 'Error testing Image Gen'}</span>`;
                }
            } catch (err) {
                resultDiv.innerHTML = `<span class="text-danger">Error: ${err.message}</span>`;
            }
        });
    }

    const testSafetyBtn = document.getElementById('test_safety_button');
    if (testSafetyBtn) {
        testSafetyBtn.addEventListener('click', async () => {
            const resultDiv = document.getElementById('test_safety_result');
            resultDiv.innerHTML = 'Testing Safety...';

            const contentSafetyEnabled = document.getElementById('enable_content_safety').checked;
            const enableApim = document.getElementById('enable_content_safety_apim').checked;

            const payload = {
                test_type: 'safety',
                enabled: contentSafetyEnabled,
                enable_apim: enableApim
            };

            if (enableApim) {
                payload.apim = {
                    endpoint: document.getElementById('azure_apim_content_safety_endpoint').value,
                    subscription_key: document.getElementById('azure_apim_content_safety_subscription_key').value,
                    deployment: document.getElementById('azure_apim_content_safety_deployment').value,
                    api_version: document.getElementById('azure_apim_content_safety_api_version').value
                };
            } else {
                payload.direct = {
                    endpoint: document.getElementById('content_safety_endpoint').value,
                    auth_type: document.getElementById('content_safety_authentication_type').value,
                    key: document.getElementById('content_safety_key').value
                };
            }

            try {
                const resp = await fetch('/api/admin/settings/test_connection', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await resp.json();
                if (resp.ok) {
                    resultDiv.innerHTML = `<span class="text-success">${data.message}</span>`;
                } else {
                    resultDiv.innerHTML = `<span class="text-danger">${data.error || 'Error testing Safety'}</span>`;
                }
            } catch (err) {
                resultDiv.innerHTML = `<span class="text-danger">Error: ${err.message}</span>`;
            }
        });
    }

    const testWebSearchBtn = document.getElementById('test_web_search_button');
    if (testWebSearchBtn) {
        testWebSearchBtn.addEventListener('click', async () => {
            const resultDiv = document.getElementById('test_web_search_result');
            resultDiv.innerHTML = 'Testing Bing Web Search...';

            const webSearchEnabled = document.getElementById('enable_web_search').checked;
            const enableApim = document.getElementById('enable_web_search_apim').checked;

            const payload = {
                test_type: 'web_search',
                enabled: webSearchEnabled,
                enable_apim: enableApim
            };

            if (enableApim) {
                payload.apim = {
                    endpoint: document.getElementById('azure_apim_web_search_endpoint').value,
                    subscription_key: document.getElementById('azure_apim_web_search_subscription_key').value,
                    deployment: document.getElementById('azure_apim_web_search_deployment').value,
                    api_version: document.getElementById('azure_apim_web_search_api_version').value
                };
            } else {
                payload.direct = {
                    key: document.getElementById('bing_search_key').value
                };
            }

            try {
                const resp = await fetch('/api/admin/settings/test_connection', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await resp.json();
                if (resp.ok) {
                    resultDiv.innerHTML = `<span class="text-success">${data.message}</span>`;
                } else {
                    resultDiv.innerHTML = `<span class="text-danger">${data.error || 'Error testing Web Search'}</span>`;
                }
            } catch (err) {
                resultDiv.innerHTML = `<span class="text-danger">Error: ${err.message}</span>`;
            }
        });
    }

    const testAzureSearchBtn = document.getElementById('test_azure_ai_search_button');
    if (testAzureSearchBtn) {
        testAzureSearchBtn.addEventListener('click', async () => {
            const resultDiv = document.getElementById('test_azure_ai_search_result');
            resultDiv.innerHTML = 'Testing Azure AI Search...';

            const enableApim = document.getElementById('enable_ai_search_apim').checked;

            const payload = {
                test_type: 'azure_ai_search',
                enable_apim: enableApim
            };

            if (enableApim) {
                payload.apim = {
                    endpoint: document.getElementById('azure_apim_ai_search_endpoint').value,
                    subscription_key: document.getElementById('azure_apim_ai_search_subscription_key').value,
                    deployment: document.getElementById('azure_apim_ai_search_deployment').value,
                    api_version: document.getElementById('azure_apim_ai_search_api_version').value
                };
            } else {
                payload.direct = {
                    endpoint: document.getElementById('azure_ai_search_endpoint').value,
                    auth_type: document.getElementById('azure_ai_search_authentication_type').value,
                    key: document.getElementById('azure_ai_search_key').value
                };
            }

            try {
                const resp = await fetch('/api/admin/settings/test_connection', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await resp.json();
                if (resp.ok) {
                    resultDiv.innerHTML = `<span class="text-success">${data.message}</span>`;
                } else {
                    resultDiv.innerHTML = `<span class="text-danger">${data.error || 'Error testing Azure AI Search'}</span>`;
                }
            } catch (err) {
                resultDiv.innerHTML = `<span class="text-danger">Error: ${err.message}</span>`;
            }
        });
    }

    const testDocIntelBtn = document.getElementById('test_azure_doc_intelligence_button');
    if (testDocIntelBtn) {
        testDocIntelBtn.addEventListener('click', async () => {
            const resultDiv = document.getElementById('test_azure_doc_intelligence_result');
            resultDiv.innerHTML = 'Testing Document Intelligence...';

            const enableApim = document.getElementById('enable_document_intelligence_apim').checked;

            const payload = {
                test_type: 'azure_doc_intelligence',
                enable_apim: enableApim
            };

            if (enableApim) {
                payload.apim = {
                    endpoint: document.getElementById('azure_apim_document_intelligence_endpoint').value,
                    subscription_key: document.getElementById('azure_apim_document_intelligence_subscription_key').value,
                    deployment: document.getElementById('azure_apim_document_intelligence_deployment').value,
                    api_version: document.getElementById('azure_apim_document_intelligence_api_version').value
                };
            } else {
                payload.direct = {
                    endpoint: document.getElementById('azure_document_intelligence_endpoint').value,
                    auth_type: document.getElementById('azure_document_intelligence_authentication_type').value,
                    key: document.getElementById('azure_document_intelligence_key').value
                };
            }

            try {
                const resp = await fetch('/api/admin/settings/test_connection', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await resp.json();
                if (resp.ok) {
                    resultDiv.innerHTML = `<span class="text-success">${data.message}</span>`;
                } else {
                    resultDiv.innerHTML = `<span class="text-danger">${data.error || 'Error testing Doc Intelligence'}</span>`;
                }
            } catch (err) {
                resultDiv.innerHTML = `<span class="text-danger">Error: ${err.message}</span>`;
            }
        });
    }
}

function toggleEnhancedCitation(isEnabled) {
    const container = document.getElementById('enhanced_citation_settings');
    if (!container) return;
    container.style.display = isEnabled ? 'block' : 'none';
}


function switchTab(event, tabButtonId) {
    event.preventDefault();
    const triggerEl = document.getElementById(tabButtonId);
    const tabObj = new bootstrap.Tab(triggerEl);
    tabObj.show();
  }

function togglePassword(btnId, inputId) {
    const btn = document.getElementById(btnId);
    const inp = document.getElementById(inputId);
    if (btn && inp) {
        btn.addEventListener('click', function () {
            if (inp.type === 'password') {
                inp.type = 'text';
                this.textContent = 'Hide';
            } else {
                inp.type = 'password';
                this.textContent = 'Show';
            }
        });
    }
}

togglePassword('toggle_gpt_key', 'azure_openai_gpt_key');
togglePassword('toggle_embedding_key', 'azure_openai_embedding_key');
togglePassword('toggle_image_gen_key', 'azure_openai_image_gen_key');
togglePassword('toggle_content_safety_key', 'content_safety_key');
togglePassword('toggle_bing_search_key', 'bing_search_key');
togglePassword('toggle_search_key', 'azure_ai_search_key');
togglePassword('toggle_docintel_key', 'azure_document_intelligence_key');
togglePassword('toggle_azure_apim_gpt_subscription_key', 'azure_apim_gpt_subscription_key');
togglePassword('toggle_azure_apim_embedding_subscription_key', 'azure_apim_embedding_subscription_key');
togglePassword('toggle_azure_apim_image_gen_subscription_key', 'azure_apim_image_gen_subscription_key');
togglePassword('toggle_azure_apim_content_safety_subscription_key', 'azure_apim_content_safety_subscription_key');
togglePassword('toggle_azure_apim_web_search_subscription_key', 'azure_apim_web_search_subscription_key');
togglePassword('toggle_azure_apim_ai_search_subscription_key', 'azure_apim_ai_search_subscription_key');
togglePassword('toggle_azure_apim_document_intelligence_subscription_key', 'azure_apim_document_intelligence_subscription_key');
togglePassword('toggle_office_docs_key', 'office_docs_key');
togglePassword('toggle_video_files_key', 'video_files_key');
togglePassword('toggle_audio_files_key', 'audio_files_key');