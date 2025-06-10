// script.js
let pipelines = [];
let currentPipelineId = null; // Used to track which pipeline is being edited
let nextPipelineId = 1;    // Auto-incrementing ID for pipeline
let nextInputId = 1;     // Auto-incrementing ID for input
let nextSinkId = 1;      // Auto-incrementing ID for sink
let activePipelineBox = null; // Variable to track the currently expanded pipeline

function showPipelineForm(pipelineId = null) {
  document.getElementById("inputList").innerHTML = "";
  currentPipelineId = pipelineId;

  const modalTitle = document.getElementById("modal-title");

  if (pipelineId === null) {
    modalTitle.textContent = "New Pipeline Configuration";
    addInputConfig(); // Always add at least one input for new pipeline
  } else {
    modalTitle.textContent = `Edit Pipeline ID: ${pipelineId}`;
    const pipelineToEdit = pipelines.find(p => p.id === pipelineId);
    if (pipelineToEdit && pipelineToEdit.inputs && pipelineToEdit.inputs.length > 0) {
      pipelineToEdit.inputs.forEach(input => addInputConfig(input));
    } else {
      addInputConfig(); // If pipeline has no inputs, add one when editing
    }
  }
  document.getElementById("pipelineModal").style.display = "flex";
}

function closeModal() {
  document.getElementById("pipelineModal").style.display = "none";
  currentPipelineId = null;
}

function addInputConfig(inputData = {}) {
  const div = document.createElement("div");
  const inputId = inputData.id || `input-${nextInputId++}`;
  div.className = "input-block";
  div.setAttribute("data-input-id", inputId);

  div.innerHTML = `
    <h4>Input Configuration <button class="delete-input-btn" onclick="deleteInputConfig('${inputId}')">X</button></h4>
    <label for="log_type_${inputId}">Log Type <span class="required">*</span></label>
    <select id="log_type_${inputId}" name="log_type" required onchange="updateDefaultSinkValues(this, '${inputId}')">
      <option value="">Select Log Type</option>
      <option value="error_log" ${inputData.log_type === 'error_log' ? 'selected' : ''}>Error Log</option>
      <option value="cisco_log" ${inputData.log_type === 'cisco_log' ? 'selected' : ''}>Cisco Log</option>
      <option value="access_log" ${inputData.log_type === 'access_log' ? 'selected' : ''}>Access Log</option>
      <option value="window_log" ${inputData.log_type === 'window_log' ? 'selected' : ''}>Window Log</option>
    </select>

    <label><input type="checkbox" name="enrich_geoip" ${inputData.enrich_geoip ? 'checked' : ''}> Enrich GeoIP</label>
    <label><input type="checkbox" name="enrich_threatip" ${inputData.enrich_threatip ? 'checked' : ''}> Enrich ThreatIP</label>

    <div class="sink-section">
      <h4>Sinks</h4>
      <div id="sinkList-${inputId}"></div>
      <button class="btn add-sink-btn" onclick="addSinkConfig('${inputId}')">+ Add Sink</button>
    </div>
    <hr class="input-divider">
  `;
  document.getElementById("inputList").appendChild(div);

  // Load existing sinks if editing
  if (inputData.sinks && inputData.sinks.length > 0) {
    inputData.sinks.forEach(sink => addSinkConfig(inputId, sink));
  }
}

function addSinkConfig(inputId, sinkData = {}) {
  const sinkList = document.getElementById(`sinkList-${inputId}`);
  if (!sinkList) return;

  const sinkBlock = document.createElement("div");
  const sinkId = sinkData.id || `sink-${nextSinkId++}`;
  sinkBlock.className = "sink-block-modal";
  sinkBlock.setAttribute("data-sink-id", sinkId);

  const isElasticsearch = sinkData.type === 'elasticsearch';
  const isAwsS3 = sinkData.type === 'aws_s3';

  // Default values for new sinks
  const defaultEsEndpoint = 'http://elasticsearch:9200';
  const defaultS3Endpoint = 'http://minio:9000';
  const defaultS3Bucket = 'log-bucket'; // Mặc định cho Bucket
  const defaultS3AccessKeyId = 'minio';
  const defaultS3SecretAccessKey = 'minio123';
  const defaultS3Region = 'us-east-1'; // Mặc định cho Region
  const defaultS3KeyPrefix = "year=%Y/month=%m/day=%d/"; // Giá trị mặc định cho Key Prefix

  // Determine initial values for input fields in the modal
  const esEndpointValue = sinkData.config?.endpoint || defaultEsEndpoint;
  const esIndexValue = sinkData.config?.index || ''; // Sẽ được cập nhật bằng updateDefaultSinkValues
  const s3EndpointValue = sinkData.config?.endpoint || defaultS3Endpoint;
  const s3BucketValue = sinkData.config?.bucket || defaultS3Bucket;
  const s3KeyPrefixValue = sinkData.config?.key_prefix || defaultS3KeyPrefix; // Điền mặc định vào input
  const s3AccessKeyIdValue = sinkData.config?.auth?.access_key_id || defaultS3AccessKeyId;
  const s3SecretAccessKeyValue = sinkData.config?.auth?.secret_access_key || defaultS3SecretAccessKey;
  const s3RegionValue = sinkData.config?.region || defaultS3Region;


  sinkBlock.innerHTML = `
    <div class="sink-header">
      <label>
        <input type="radio" name="sink_type_${sinkId}" value="elasticsearch"
               onchange="toggleSinkFields('${sinkId}', 'elasticsearch')" ${isElasticsearch ? 'checked' : ''}>
        Sink to Elasticsearch <span class="required">*</span>
      </label>
      <label>
        <input type="radio" name="sink_type_${sinkId}" value="aws_s3"
               onchange="toggleSinkFields('${sinkId}', 'aws_s3')" ${isAwsS3 ? 'checked' : ''}>
        Sink to AWS S3 <span class="required">*</span>
      </label>
      <button class="delete-input-btn" onclick="deleteSinkConfig('${inputId}', '${sinkId}')">X</button>
    </div>
    <div id="esFields-${sinkId}" class="sink-fields" style="display: ${isElasticsearch ? 'block' : 'none'};">
      <label for="es_endpoint_${sinkId}">Endpoint <span class="required">*</span></label>
      <input type="text" id="es_endpoint_${sinkId}" name="es_endpoint" placeholder="http://elasticsearch:9200" value="${esEndpointValue}" ${isElasticsearch ? 'required' : ''}>
      <label for="es_index_${sinkId}">Index <span class="required">*</span></label>
      <input type="text" id="es_index_${sinkId}" name="es_index" placeholder="e.g., {{ log_type }}" value="${esIndexValue}" ${isElasticsearch ? 'required' : ''}>
    </div>
    <div id="s3Fields-${sinkId}" class="sink-fields" style="display: ${isAwsS3 ? 'block' : 'none'};">
        <label for="s3_endpoint_${sinkId}">Endpoint <span class="required">*</span></label>
        <input type="text" id="s3_endpoint_${sinkId}" name="s3_endpoint" placeholder="http://minio:9000" value="${s3EndpointValue}" ${isAwsS3 ? 'required' : ''}>

        <div class="form-row">
            <div class="form-group">
                <label for="s3_bucket_${sinkId}">Bucket <span class="required">*</span></label>
                <input type="text" id="s3_bucket_${sinkId}" name="s3_bucket" placeholder="Bucket (e.g., log-bucket)" value="${s3BucketValue}" ${isAwsS3 ? 'required' : ''}>
            </div>
            <div class="form-group">
                <label for="s3_region_${sinkId}">Region <span class="required">*</span></label>
                <select id="s3_region_${sinkId}" name="s3_region" required>
                    <option value="us-east-1" ${s3RegionValue === 'us-east-1' ? 'selected' : ''}>us-east-1</option>
                    <option value="us-east-2" ${s3RegionValue === 'us-east-2' ? 'selected' : ''}>us-east-2</option>
                    <option value="us-west-1" ${s3RegionValue === 'us-west-1' ? 'selected' : ''}>us-west-1</option>
                    <option value="us-west-2" ${s3RegionValue === 'us-west-2' ? 'selected' : ''}>us-west-2</option>
                    <option value="eu-west-1" ${s3RegionValue === 'eu-west-1' ? 'selected' : ''}>eu-west-1</option>
                </select>
            </div>
        </div>

        <label for="s3_key_${sinkId}">Key Prefix <span class="required">*</span></label>
        <input type="text" id="s3_key_${sinkId}" name="s3_key" placeholder="e.g., year=%Y/month=%m/day=%d/{{ log_type }}/" value="${s3KeyPrefixValue}" ${isAwsS3 ? 'required' : ''}>

        <div class="form-row">
            <div class="form-group">
                <label for="s3_access_key_id_${sinkId}">Access Key ID <span class="required">*</span></label>
                <input type="text" id="s3_access_key_id_${sinkId}" name="s3_access_key_id" placeholder="Access Key ID" value="${s3AccessKeyIdValue}" ${isAwsS3 ? 'required' : ''}>
            </div>
            <div class="form-group">
                <label for="s3_secret_access_key_${sinkId}">Secret Access Key <span class="required">*</span></label>
                <input type="text" id="s3_secret_access_key_${sinkId}" name="s3_secret_access_key" placeholder="Secret Access Key" value="${s3SecretAccessKeyValue}" ${isAwsS3 ? 'required' : ''}>
            </div>
        </div>
    </div>
    <hr class="sink-divider">
  `;
  sinkList.appendChild(sinkBlock);

  // Initially set required for the checked sink type
  if (isElasticsearch) {
      toggleSinkFields(sinkId, 'elasticsearch');
  } else if (isAwsS3) {
      toggleSinkFields(sinkId, 'aws_s3');
  }

  // Cập nhật giá trị mặc định khi thêm sink, dựa trên log_type hiện tại
  const logTypeSelect = document.getElementById(`log_type_${inputId}`);
  if (logTypeSelect) {
      updateDefaultSinkValues(logTypeSelect, inputId, sinkId);
  }
}

function updateDefaultSinkValues(logTypeSelect, inputId, specificSinkId = null) {
    const logType = logTypeSelect.value;
    const sanitizedLogType = logType ? logType.toLowerCase().replace(/ /g, '_') : '';

    const sinkBlocks = specificSinkId
        ? [document.querySelector(`.sink-block-modal[data-sink-id="${specificSinkId}"]`)]
        : document.querySelectorAll(`#sinkList-${inputId} .sink-block-modal`);

    sinkBlocks.forEach(sinkBlock => {
        const sinkId = sinkBlock.getAttribute("data-sink-id");
        const selectedSinkType = sinkBlock.querySelector('input[name^="sink_type_"]:checked');

        if (selectedSinkType && selectedSinkType.value === 'elasticsearch') {
            const esIndexInput = document.getElementById(`es_index_${sinkId}`);
            if (esIndexInput && !esIndexInput.value) { // Chỉ cập nhật nếu trường trống
                esIndexInput.value = sanitizedLogType;
            }
        } else if (selectedSinkType && selectedSinkType.value === 'aws_s3') {
            const s3KeyInput = document.getElementById(`s3_key_${sinkId}`);
            const s3BucketInput = document.getElementById(`s3_bucket_${sinkId}`);

            if (s3KeyInput && !s3KeyInput.value) { // Chỉ cập nhật nếu trường trống
                s3KeyInput.value = `year=%Y/month=%m/day=%d/${sanitizedLogType}/`;
            }
            if (s3BucketInput && !s3BucketInput.value) { // Chỉ cập nhật nếu trường trống
                s3BucketInput.value = 'log-bucket'; // Mặc định cho Bucket
            }
        }
    });
}


function toggleSinkFields(sinkId, sinkType) {
  const esFields = document.getElementById(`esFields-${sinkId}`);
  const s3Fields = document.getElementById(`s3Fields-${sinkId}`);

  const esEndpointInput = document.getElementById(`es_endpoint_${sinkId}`);
  const esIndexInput = document.getElementById(`es_index_${sinkId}`);
  const s3EndpointInput = document.getElementById(`s3_endpoint_${sinkId}`);
  const s3BucketInput = document.getElementById(`s3_bucket_${sinkId}`);
  const s3KeyInput = document.getElementById(`s3_key_${sinkId}`);
  const s3AccessKeyIdInput = document.getElementById(`s3_access_key_id_${sinkId}`);
  const s3SecretAccessKeyInput = document.getElementById(`s3_secret_access_key_${sinkId}`);
  const s3RegionSelect = document.getElementById(`s3_region_${sinkId}`); // Changed to select

  // Helper to set/remove required attribute
  const setRequired = (input, isRequired) => {
      if (input) {
          if (isRequired) {
              input.setAttribute('required', 'true');
          } else {
              input.removeAttribute('required');
          }
      }
  };

  if (sinkType === 'elasticsearch') {
    esFields.style.display = 'block';
    s3Fields.style.display = 'none';

    setRequired(esEndpointInput, true);
    setRequired(esIndexInput, true);

    setRequired(s3EndpointInput, false);
    setRequired(s3BucketInput, false);
    setRequired(s3KeyInput, false);
    setRequired(s3AccessKeyIdInput, false);
    setRequired(s3SecretAccessKeyInput, false);
    setRequired(s3RegionSelect, false); // Changed to select

  } else if (sinkType === 'aws_s3') {
    esFields.style.display = 'none';
    s3Fields.style.display = 'block';

    setRequired(esEndpointInput, false);
    setRequired(esIndexInput, false);

    setRequired(s3EndpointInput, true);
    setRequired(s3BucketInput, true);
    setRequired(s3KeyInput, true);
    setRequired(s3AccessKeyIdInput, true);
    setRequired(s3SecretAccessKeyInput, true);
    setRequired(s3RegionSelect, true); // Changed to select
  }
}

function deleteInputConfig(inputId) {
  const inputBlock = document.querySelector(`.input-block[data-input-id="${inputId}"]`);
  if (inputBlock) {
    inputBlock.remove();
  }

  // Issue 1 Fix: After deleting an input, if there are no inputs left, add a new one
  if (document.querySelectorAll("#inputList .input-block").length === 0) {
      addInputConfig();
  }
}

function deleteSinkConfig(inputId, sinkId) {
  const sinkBlock = document.querySelector(`#sinkList-${inputId} .sink-block-modal[data-sink-id="${sinkId}"]`);
  if (sinkBlock) {
    sinkBlock.remove();
  }
}

function submitPipeline() {
  const inputs = document.querySelectorAll("#inputList .input-block");
  const pipelineInputsData = [];

  let isValid = true; // Flag for validation

  inputs.forEach(inputBlock => {
    // Validate Log Type
    const logTypeSelect = inputBlock.querySelector("select[name='log_type']");
    const logTypeValue = logTypeSelect.value;
    if (!logTypeValue) {
        isValid = false;
        logTypeSelect.classList.add('error-field'); // Add error class for styling
    } else {
        logTypeSelect.classList.remove('error-field');
    }

    const inputSinksData = [];
    const sinkBlocks = inputBlock.querySelectorAll(".sink-block-modal");

    sinkBlocks.forEach(sinkBlock => {
      const selectedSinkType = sinkBlock.querySelector('input[name^="sink_type_"]:checked');

      // Validate Sink Type selection
      if (!selectedSinkType) {
          isValid = false;
          sinkBlock.querySelector('.sink-header').classList.add('error-field'); // Add error class
          return; // Skip this sink block if no type selected
      } else {
          sinkBlock.querySelector('.sink-header').classList.remove('error-field');
      }

      const sinkData = {
        id: sinkBlock.getAttribute("data-sink-id"),
        type: selectedSinkType.value,
        config: {}
      };

      if (selectedSinkType.value === 'elasticsearch') {
        const esEndpointInput = sinkBlock.querySelector("input[name='es_endpoint']");
        const esIndexInput = sinkBlock.querySelector("input[name='es_index']");

        if (!esEndpointInput.value) {
            isValid = false;
            esEndpointInput.classList.add('error-field');
        } else {
            esEndpointInput.classList.remove('error-field');
            sinkData.config.endpoint = esEndpointInput.value;
        }

        if (!esIndexInput.value && logTypeValue) { // Nếu index trống và logType đã chọn, dùng mặc định
            sinkData.config.index = logTypeValue.toLowerCase().replace(/ /g, '_');
            esIndexInput.classList.remove('error-field'); // Xóa lỗi nếu tự động điền
        } else if (!esIndexInput.value && !logTypeValue) { // Nếu index trống và logType cũng trống (lỗi)
            isValid = false;
            esIndexInput.classList.add('error-field');
        } else {
            esIndexInput.classList.remove('error-field');
            sinkData.config.index = esIndexInput.value;
        }

      } else if (selectedSinkType.value === 'aws_s3') {
        const s3EndpointInput = sinkBlock.querySelector("input[name='s3_endpoint']");
        const s3BucketInput = sinkBlock.querySelector("input[name='s3_bucket']");
        const s3KeyInput = sinkBlock.querySelector("input[name='s3_key']");
        const s3AccessKeyIdInput = sinkBlock.querySelector("input[name='s3_access_key_id']");
        const s3SecretAccessKeyInput = sinkBlock.querySelector("input[name='s3_secret_access_key']");
        const s3RegionSelect = sinkBlock.querySelector("select[name='s3_region']"); // Changed to select


        if (!s3EndpointInput.value) {
            isValid = false;
            s3EndpointInput.classList.add('error-field');
        } else {
            s3EndpointInput.classList.remove('error-field');
            sinkData.config.endpoint = s3EndpointInput.value;
        }

        if (!s3BucketInput.value) { // Nếu Bucket trống, dùng mặc định
            sinkData.config.bucket = 'log-bucket';
            s3BucketInput.classList.remove('error-field'); // Xóa lỗi nếu tự động điền
        } else {
            s3BucketInput.classList.remove('error-field');
            sinkData.config.bucket = s3BucketInput.value;
        }

        if (!s3KeyInput.value && logTypeValue) { // Nếu Key Prefix trống và logType đã chọn, dùng mặc định
            sinkData.config.key_prefix = `year=%Y/month=%m/day=%d/${logTypeValue.toLowerCase().replace(/ /g, '_')}/`;
            s3KeyInput.classList.remove('error-field'); // Xóa lỗi nếu tự động điền
        } else if (!s3KeyInput.value && !logTypeValue) { // Nếu Key Prefix trống và logType cũng trống (lỗi)
            isValid = false;
            s3KeyInput.classList.add('error-field');
        } else {
            s3KeyInput.classList.remove('error-field');
            sinkData.config.key_prefix = s3KeyInput.value;
        }

        sinkData.config.auth = {};
        if (!s3AccessKeyIdInput.value) {
            isValid = false;
            s3AccessKeyIdInput.classList.add('error-field');
        } else {
            s3AccessKeyIdInput.classList.remove('error-field');
            sinkData.config.auth.access_key_id = s3AccessKeyIdInput.value;
        }

        if (!s3SecretAccessKeyInput.value) {
            isValid = false;
            s3SecretAccessKeyInput.classList.add('error-field');
        } else {
            s3SecretAccessKeyInput.classList.remove('error-field');
            sinkData.config.auth.secret_access_key = s3SecretAccessKeyInput.value;
        }

        if (!s3RegionSelect.value) {
            isValid = false;
            s3RegionSelect.classList.add('error-field');
        } else {
            s3RegionSelect.classList.remove('error-field');
            sinkData.config.region = s3RegionSelect.value;
        }

        // Thêm các trường cố định khác như force_path_style, compression, encoding, batch, buffer
        // sinkData.config.force_path_style = true;
        // sinkData.config.compression = 'gzip';
        // sinkData.config.content_encoding = 'gzip';
        // sinkData.config.filename_extension = 'gz';
        // sinkData.config.content_type = 'application/json';
        // sinkData.config.buffer = {
        //     type: 'disk',
        //     max_size: 268435490,
        //     when_full: 'block'
        // };
        // sinkData.config.batch = {
        //     max_events: 10,
        //     max_timeout_secs: 10
        // };
        // sinkData.config.encoding = {
        //     codec: 'json'
        // };

      }
      inputSinksData.push(sinkData);
    });

    const data = {
      id: inputBlock.getAttribute("data-input-id"),
      log_type: logTypeValue, // Use logTypeValue here
      enrich_geoip: inputBlock.querySelector("input[name='enrich_geoip']").checked,
      enrich_threatip: inputBlock.querySelector("input[name='enrich_threatip']").checked,
      sinks: inputSinksData // Use "sinks" array
    };
    pipelineInputsData.push(data);
  });

  if (!isValid) {
      alert('Please fill in all required fields and select a sink type for all sinks.');
      return;
  }

  if (currentPipelineId === null) {
    const newPipeline = {
      id: nextPipelineId++,
      inputs: pipelineInputsData,
      isRunning: false
    };
    pipelines.push(newPipeline);
  } else {
    const pipelineIndex = pipelines.findIndex(p => p.id === currentPipelineId);
    if (pipelineIndex !== -1) {
      pipelines[pipelineIndex].inputs = pipelineInputsData;
    }
  }

  renderAllPipelines();
  closeModal();

  // Đảm bảo pipeline đang được chỉnh sửa vẫn mở sau khi cập nhật
  if (currentPipelineId !== null) {
    const editedPipelineBox = document.querySelector(`.pipeline-box[data-pipeline-id="${currentPipelineId}"]`);
    if (editedPipelineBox) {
        editedPipelineBox.classList.remove('collapsed');
        activePipelineBox = editedPipelineBox;
    }
  }
}

// script.js
// ... (các hàm và biến khác không đổi)

function renderAllPipelines() {
  const container = document.getElementById("pipelines");
  if (!container) return;
  container.innerHTML = "";

  const pipelineConfigSection = document.getElementById("pipeline-config-section");
  if (pipelineConfigSection && pipelineConfigSection.classList.contains('active')) {
      let sectionTitle = pipelineConfigSection.querySelector('.section-title');
      if (!sectionTitle) {
          sectionTitle = document.createElement('h2');
          sectionTitle.className = 'section-title';
          sectionTitle.textContent = 'Pipeline Configuration';
          pipelineConfigSection.prepend(sectionTitle);
      }
  }

  const addPipelineBtnContainer = document.getElementById("add-pipeline-btn-container");
  if (pipelines.length === 0) {
      addPipelineBtnContainer.classList.add('empty-state');
      if (pipelineConfigSection && addPipelineBtnContainer) {
          const title = pipelineConfigSection.querySelector('.section-title');
          if (title) {
              title.after(addPipelineBtnContainer);
          } else {
              pipelineConfigSection.prepend(addPipelineBtnContainer);
          }
      }
  } else {
      addPipelineBtnContainer.classList.remove('empty-state');
      if (pipelineConfigSection && addPipelineBtnContainer) {
          pipelineConfigSection.appendChild(addPipelineBtnContainer);
      }
  }

  pipelines.forEach(pipeline => {
    const box = document.createElement("div");
    box.className = `pipeline-box ${pipeline.isRunning ? 'running' : ''}`;
    box.setAttribute("data-pipeline-id", pipeline.id);

    const header = document.createElement("div");
    header.className = "pipeline-header";
    header.innerHTML = `<h3>Pipeline ID: ${pipeline.id}</h3>`;
    box.appendChild(header);

    const columnHeaders = document.createElement("div");
    columnHeaders.className = "pipeline-column-headers";
    columnHeaders.innerHTML = `
        <div class="header-cell logtype-cell-header">Log Type</div>
        <div class="header-cell enrich-cell-header">Enrich</div>
        <div class="header-cell sink-cell-header">Sink</div>
    `;
    box.appendChild(columnHeaders);

    const pipelineContent = document.createElement("div");
    pipelineContent.className = "pipeline-content";

    pipeline.inputs.forEach(input => {
      const inputRow = document.createElement("div");
      inputRow.className = "pipeline-input-row";

      const logTypeCell = document.createElement("div");
      logTypeCell.className = "pipeline-cell logtype-cell";
      const logTypeBlock = document.createElement("div");
      logTypeBlock.className = "block logtype-block-content";

      let displayLogType = input.log_type.replace('_', ' ').split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
      logTypeBlock.innerHTML = `<strong>${displayLogType}</strong>`;
      logTypeCell.appendChild(logTypeBlock);
      inputRow.appendChild(logTypeCell);

      const enrichCell = document.createElement("div");
      enrichCell.className = "pipeline-cell enrich-cell";
      const enrichContainer = document.createElement("div");
      enrichContainer.className = "enrich-container";

      const enrichBlocks = [];

      if (input.enrich_geoip) {
        const geoipBlock = document.createElement("div");
        geoipBlock.className = "block enrich-block geoip-enrich";
        geoipBlock.innerHTML = `<img src="https://img.icons8.com/ios-filled/24/000000/globe--v1.png" alt="GeoIP"> GeoIP`;
        enrichBlocks.push(geoipBlock);
      }
      if (input.enrich_threatip) {
        const threatipBlock = document.createElement("div");
        threatipBlock.className = "block enrich-block threatip-enrich";
        threatipBlock.innerHTML = `<img src="https://img.icons8.com/ios-filled/24/000000/shield.png" alt="ThreatIP"> ThreatIP`;
        enrichBlocks.push(threatipBlock);
      }

      if (enrichBlocks.length > 0) {
        enrichBlocks.forEach(block => enrichContainer.appendChild(block));
      } else {
          const noEnrich = document.createElement("div");
          noEnrich.className = "block no-enrich-display";
          noEnrich.textContent = "No Enrich";
          enrichContainer.appendChild(noEnrich);
      }

      enrichCell.appendChild(enrichContainer);
      inputRow.appendChild(enrichCell);

      const sinkCell = document.createElement("div");
      sinkCell.className = "pipeline-cell sink-display-cell";

      const inputSinksContainer = document.createElement("div");
      inputSinksContainer.className = "input-sinks-container-display";

      if (input.sinks && input.sinks.length > 0) {
        input.sinks.forEach(sink => {
          if (sink.type === 'elasticsearch') {
            const esSink = document.createElement("div");
            esSink.className = "block sink-block es-sink";
            esSink.innerHTML = `
              <img src="https://img.icons8.com/color/24/000000/elasticsearch.png" alt="Elasticsearch">
              <div>
                <strong>Elasticsearch</strong><br>
                Endpoint: ${sink.config.endpoint}<br>
                Index: ${sink.config.index}
              </div>
            `;
            inputSinksContainer.appendChild(esSink);
          } else if (sink.type === 'aws_s3') {
            const s3Sink = document.createElement("div");
            s3Sink.className = "block sink-block s3-sink";
            s3Sink.innerHTML = `
              <img src="https://img.icons8.com/color/24/000000/amazon-s3.png" alt="AWS S3">
              <div>
                <strong>AWS S3</strong><br>
                Endpoint: ${sink.config.endpoint}<br>
                Bucket: ${sink.config.bucket}
              </div>
            `;
            inputSinksContainer.appendChild(s3Sink);
          }
        });
      } else {
        const noSink = document.createElement("div");
        noSink.className = "block no-sink-display";
        noSink.textContent = "No Sink";
        inputSinksContainer.appendChild(noSink);
      }

      sinkCell.appendChild(inputSinksContainer);
      inputRow.appendChild(sinkCell);

      pipelineContent.appendChild(inputRow);
    });

    box.appendChild(pipelineContent);

    const controls = document.createElement("div");
    controls.className = "pipeline-controls";

    // Thêm nút Edit
    const editButton = document.createElement("button");
    editButton.className = `btn ${pipeline.isRunning ? 'disabled-edit-btn' : ''}`; // Thêm class disabled-edit-btn nếu đang chạy
    editButton.textContent = "Edit";
    editButton.onclick = () => {
        if (!pipeline.isRunning) { // Chỉ cho phép chỉnh sửa nếu pipeline không chạy
            showPipelineForm(pipeline.id);
        }
    };
    controls.appendChild(editButton);

    // Thêm nút Run/Stop
    const toggleRunButton = document.createElement("button");
    toggleRunButton.className = `btn ${pipeline.isRunning ? 'stop-btn' : 'run-btn'}`;
    toggleRunButton.textContent = pipeline.isRunning ? 'Stop' : 'Run';
    toggleRunButton.onclick = () => togglePipelineRun(pipeline.id);
    controls.appendChild(toggleRunButton);

    // Thêm nút Delete
    const deleteButton = document.createElement("button");
    deleteButton.className = "btn cancel-btn";
    deleteButton.textContent = "Delete";
    deleteButton.onclick = () => deletePipeline(pipeline.id);
    controls.appendChild(deleteButton);

    box.appendChild(controls);

    container.appendChild(box);
  });
}

// ... (các hàm và biến khác không đổi)
function togglePipelineExpand(pipelineBox) {
    // If another pipeline is open, collapse it
    if (activePipelineBox && activePipelineBox !== pipelineBox) {
        activePipelineBox.classList.add('collapsed');
    }

    // Toggle the current pipeline's state
    pipelineBox.classList.toggle('collapsed');

    // Update the active pipeline
    if (pipelineBox.classList.contains('collapsed')) {
        activePipelineBox = null;
    } else {
        activePipelineBox = pipelineBox;
    }
}

document.addEventListener('click', function(event) {
    const modal = document.getElementById('pipelineModal');
    const isClickInsideModal = modal.contains(event.target);
    const clickedPipelineBox = event.target.closest('.pipeline-box');
    const isClickInsideSidebar = event.target.closest('.sidebar');
    const isClickOnPipelineControlBtn = event.target.closest('.pipeline-controls .btn');
    const isClickOnAddPipelineBtn = event.target.closest('.add-large-btn'); // Nút + Add Pipeline

    // 1. Nếu click vào nút "Add Pipeline", không làm gì với trạng thái collapse
    if (isClickOnAddPipelineBtn) {
        return;
    }

    // 2. Nếu click vào nút Run/Stop/Edit/Delete trên một pipeline
    if (isClickOnPipelineControlBtn) {
        // Nếu activePipelineBox là pipeline chứa nút được click, giữ nguyên trạng thái
        if (activePipelineBox && activePipelineBox.contains(event.target)) {
            return; // Đã xử lý bởi logic nút riêng, không cần thu gọn
        }
    }

    // 3. Nếu modal đang mở và click bên trong modal, không làm gì
    if (document.getElementById("pipelineModal").style.display === "flex" && isClickInsideModal) {
        return;
    }

    // 4. Nếu có một pipeline đang mở (activePipelineBox)
    if (activePipelineBox) {
        // Nếu click bên trong pipeline đang mở, không làm gì
        if (activePipelineBox.contains(event.target)) {
            return;
        }
        // Nếu click bên ngoài pipeline đang mở (và không phải sidebar, không phải modal), thì thu gọn nó
        if (!isClickInsideSidebar && !isClickInsideModal) {
            activePipelineBox.classList.add('collapsed');
            activePipelineBox = null;
        }
    } else { // 5. Nếu không có pipeline nào đang mở
        // Và click vào một pipeline-box nào đó (không phải nút điều khiển)
        if (clickedPipelineBox && !isClickOnPipelineControlBtn) {
            togglePipelineExpand(clickedPipelineBox); // Mở rộng pipeline đó
        }
    }
});


function togglePipelineRun(pipelineId) {
  const pipeline = pipelines.find(p => p.id === pipelineId);
  if (pipeline) {
    pipeline.isRunning = !pipeline.isRunning; // Cập nhật trạng thái
    renderAllPipelines(); // Render lại giao diện ngay lập tức để thấy thay đổi

    // Gửi thông tin của toàn bộ pipeline về backend
    fetch('/vector-action', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      // Gửi toàn bộ đối tượng pipeline, backend sẽ phân tích 'action' (run/stop)
      // và sử dụng thông tin cấu hình bên trong.
      // Cần thêm trường 'action' để backend biết đây là thao tác 'run' hay 'stop'
      body: JSON.stringify({
          action: pipeline.isRunning ? 'start' : 'stop', // Thêm hành động cụ thể
          pipelineId: pipeline.id, // Gửi ID của pipeline
          fullPipelineConfig: pipeline // Gửi toàn bộ cấu hình pipeline
      }),
    })
    .then(response => response.json())
    .then(data => {
      console.log('Backend response:', data);
      // Bạn có thể xử lý phản hồi từ backend tại đây, ví dụ:
      // if (data.status === 'error') {
      //     alert('Failed to update pipeline status on server: ' + data.message);
      //     // Rollback UI nếu cần
      //     pipeline.isRunning = !pipeline.isRunning;
      //     renderAllPipelines();
      // }
    })
    .catch((error) => {
      console.error('Error sending pipeline status to backend:', error);
      alert('Network error or server issue. Could not update pipeline status.');
      // Rollback UI nếu có lỗi mạng
      pipeline.isRunning = !pipeline.isRunning;
      renderAllPipelines();
    });

    // Sau khi render lại, đảm bảo pipeline này vẫn mở nếu nó là activePipelineBox
    const targetPipelineBox = document.querySelector(`.pipeline-box[data-pipeline-id="${pipelineId}"]`);
    if (targetPipelineBox && activePipelineBox && activePipelineBox.dataset.pipelineId === pipelineId.toString()) {
        targetPipelineBox.classList.remove('collapsed');
        // Không cần cập nhật activePipelineBox vì nó đã được đặt ở trên
    }
  }
}

function deletePipeline(pipelineId) {
  if (confirm(`Are you sure you want to delete Pipeline ID: ${pipelineId}?`)) {
    pipelines = pipelines.filter(p => p.id !== pipelineId);
    renderAllPipelines();
    // Nếu pipeline bị xóa là pipeline đang hoạt động, reset activePipelineBox
    if (activePipelineBox && activePipelineBox.dataset.pipelineId === pipelineId.toString()) {
        activePipelineBox = null;
    }
  }
}

function showSection(sectionId, menuId) {
  const sections = document.querySelectorAll('.section');
  sections.forEach(section => {
    section.style.display = 'none';
    section.classList.remove('active');
  });

  const activeSection = document.getElementById(sectionId);
  if (activeSection) {
    activeSection.style.display = 'block';
    activeSection.classList.add('active');
  }

  const menuItems = document.querySelectorAll('.menu-item');
  menuItems.forEach(item => {
    item.classList.remove('active');
  });

  document.getElementById(menuId).classList.add('active');

  if (sectionId === 'pipeline-config-section') {
      renderAllPipelines(); // Luôn gọi render để cập nhật tiêu đề và nút Add Pipeline
  }
}

document.addEventListener("DOMContentLoaded", () => {
    showSection('pipeline-config-section', 'menu-pipeline-config');
});