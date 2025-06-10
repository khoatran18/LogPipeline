// script.js - Updated for nested sink JSON (clickhouse, elasticsearch, aws_s3)

let vectorId = 0;
let currentType = "";
let currentEditId = null;
let vectors = {};

const availableTopics = [
  "error_log_topic",
  "cisco_log_topic",
  "access_log_topic",
  "window_log_topic",
  "enrich_topic",
  "sink_topic"
];

const availableParsers = [
  "error_log",
  "cisco_log",
  "access_log",
  "window_log"
];

function formatLabel(text) {
  return text.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
}

function showForm(type, editId = null) {
  currentType = type;
  currentEditId = editId;

  document.getElementById("form-title").textContent = `${editId === null ? 'Configure' : 'Update'} ${type} Vector`;
  const formFields = document.getElementById("form-fields");
  formFields.innerHTML = "";

  let fields = [];
  let existingData = editId !== null ? structuredClone(vectors[editId].data) : {};

  if (type === "sink") {
    ["elasticsearch", "clickhouse", "aws_s3"].forEach(prefix => {
      const nested = existingData[prefix];
      if (nested) {
        existingData[`${prefix}_enabled`] = "on";
        Object.entries(nested).forEach(([k, v]) => {
          const keyName = (prefix === "aws_s3" && k === "key_prefix") ? "key" : k;
          existingData[`${prefix}_${keyName}`] = v;
        });
      }
    });
  }

  if (type === "parse") {
    fields.push({ label: "Select Source Vector", name: "source_vector", type: "select", options: availableParsers });
    fields.push({ label: "Select Source Topic(s)", name: "source_topics", type: "multicheckbox", options: availableTopics });
    fields.push({ label: "Select Sink Topic", name: "sink_topic", type: "select", options: availableTopics });
  } else if (type === "enrich") {
    fields.push({ label: "Select Source Topic(s)", name: "source_topics", type: "multicheckbox", options: availableTopics });
    fields.push({ label: "Select Sink Topic", name: "sink_topic", type: "select", options: availableTopics });
  } else if (type === "sink") {
    fields.push({ label: "Select Source Topic(s)", name: "source_topics", type: "multicheckbox", options: availableTopics });
    fields.push({ label: "Tick Elasticsearch", name: "elasticsearch_enabled", type: "checkbox", group: [
      { label: "Index", name: "elasticsearch_index", default: "{{ log_type }}" }
    ] });
    fields.push({ label: "Tick ClickHouse", name: "clickhouse_enabled", type: "checkbox", group: [
      { label: "Table", name: "clickhouse_table", default: "{{ log_type }}" }
    ] });
    fields.push({ label: "Tick S3", name: "aws_s3_enabled", type: "checkbox", group: [
      { label: "Bucket", name: "aws_s3_bucket", default: "log-bucket" },
      { label: "Key", name: "aws_s3_key", default: "year=%Y/month=%m/day=%d/{{ log_type }}/" }
    ] });
  }

  for (const field of fields) {
    const div = document.createElement("div");
    div.style.marginBottom = "15px";
    const label = document.createElement("label");
    label.textContent = field.label;
    div.appendChild(label);
    div.appendChild(document.createElement("br"));

    if (field.type === "select") {
      const input = document.createElement("select");
      input.name = field.name;
      field.options.forEach(opt => {
        const option = document.createElement("option");
        option.value = opt;
        option.textContent = formatLabel(opt);
        if (existingData[field.name] === opt) option.selected = true;
        input.appendChild(option);
      });
      div.appendChild(input);
    } else if (field.type === "multicheckbox") {
      const selected = Array.isArray(existingData[field.name]) ? existingData[field.name] : (existingData[field.name]?.split(",") || []);
      field.options.forEach(opt => {
        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.name = field.name;
        checkbox.value = opt;
        if (selected.includes(opt)) checkbox.checked = true;
        const checkboxLabel = document.createElement("label");
        checkboxLabel.textContent = formatLabel(opt);
        div.appendChild(checkbox);
        div.appendChild(checkboxLabel);
        div.appendChild(document.createElement("br"));
      });
    } else if (field.type === "checkbox" && field.group) {
      const wrapper = document.createElement("div");
      wrapper.style.border = "1px solid #ccc";
      wrapper.style.padding = "10px";
      wrapper.style.marginTop = "5px";

      const toggle = document.createElement("input");
      toggle.type = "checkbox";
      toggle.name = field.name;

      const prefix = field.name.replace("_enabled", "");
      const subData = existingData[prefix] || {};

      if (existingData[`${prefix}_enabled`] === "on") toggle.checked = true;
      toggle.onchange = () => {
        wrapper.style.display = toggle.checked ? "block" : "none";
      };

      div.appendChild(toggle);
      div.appendChild(document.createTextNode(" Enable " + field.label.replace(/^Tick /, "")));
      div.appendChild(wrapper);

      field.group.forEach(sub => {
        const subLabel = document.createElement("label");
        subLabel.textContent = sub.label;
        wrapper.appendChild(subLabel);
        wrapper.appendChild(document.createElement("br"));

        const subInput = document.createElement("input");
        subInput.name = sub.name;
        subInput.type = "text";
        subInput.value = existingData[sub.name] || sub.default || "";
        wrapper.appendChild(subInput);
        wrapper.appendChild(document.createElement("br"));
      });

      wrapper.style.display = toggle.checked ? "block" : "none";
    } else {
      const input = document.createElement("input");
      input.name = field.name;
      input.type = field.type || "text";
      input.value = existingData[field.name] || field.default || "";
      div.appendChild(input);
    }

    formFields.appendChild(div);
  }

  document.getElementById("form-modal").style.display = "flex";
}

function closeForm() {
  document.getElementById("form-modal").style.display = "none";
  currentEditId = null;
}

document.getElementById("vector-form").onsubmit = function(e) {
  e.preventDefault();
  const formData = new FormData(e.target);
  const data = {};

  for (const [key, value] of formData.entries()) {
    if (data[key]) {
      if (!Array.isArray(data[key])) {
        data[key] = [data[key]];
      }
      data[key].push(value);
    } else {
      data[key] = value;
    }
  }

  // Convert all keys that include "topics" into arrays if not already
  Object.keys(data).forEach(k => {
    if (k.includes("topics") && !Array.isArray(data[k])) {
      data[k] = [data[k]];
    }
  });

  if (currentType === "sink") {
    const output = {};
    ["elasticsearch", "clickhouse", "aws_s3"].forEach(prefix => {
      if (data[`${prefix}_enabled`] === "on") {
        const nested = {};
        Object.entries(data).forEach(([k, v]) => {
          if (k.startsWith(`${prefix}_`) && k !== `${prefix}_enabled`) {
            let newKey = k.replace(`${prefix}_`, "");
            if (prefix === "aws_s3" && newKey === "key") {
              newKey = "key_prefix";
            }
            nested[newKey] = v;
          }
        });
        output[prefix] = nested;
      }
    });

    Object.keys(data).forEach(k => {
      if (k.includes("_enabled") || /^(elasticsearch|clickhouse|aws_s3)_/.test(k)) {
        delete data[k];
      }
    });

    Object.assign(data, output);
  }

  const boxHtml = `
    <strong>${capitalize(currentType)} Vector</strong><br>
    <pre>${JSON.stringify(data, null, 2)}</pre>
    <button id="start-btn" onclick="startVector(${currentEditId ?? vectorId}, '${currentType}')" class="status_button">Start</button>
    <button id="restart-btn" onclick="restartVector(${currentEditId ?? vectorId}, '${currentType}')" class="status_button">Restart</button>
    <button id="stop-btn" onclick="stopVector(${currentEditId ?? vectorId}, '${currentType}')" class="status_button">Stop</button>
    <button id="update-btn" onclick="updateVector(${currentEditId ?? vectorId}, '${currentType}')" class="status_button">Update</button>
    <button id="delete-btn" onclick="deleteVector(${currentEditId ?? vectorId}, '${currentType}')" class="status_button">Delete</button>
  `;

  if (currentEditId !== null) {
    const newDiv = document.createElement("div");
    newDiv.className = "vector-box";
    newDiv.innerHTML = boxHtml;
    const oldDiv = vectors[currentEditId].element;
    oldDiv.parentNode.replaceChild(newDiv, oldDiv);
    vectors[currentEditId] = { data, element: newDiv };
  } else {
    const div = document.createElement("div");
    div.className = "vector-box";
    div.innerHTML = boxHtml;
    vectors[vectorId] = { data, element: div };
    document.getElementById(`${currentType}-column`).appendChild(div);
    vectorId++;
  }

  closeForm();
};

function capitalize(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

function startVector(id, type) {
  status_buttons = document.querySelectorAll(".status_button")
  status_buttons.forEach(btn => {
    btn.style.backgroundColor = "gray"
  })
  btn = document.getElementById("start-btn")
  btn.style.backgroundColor = "green"

  sendToServer("start", id, type);
}

function restartVector(id, type) {
  status_buttons = document.querySelectorAll(".status_button")
  status_buttons.forEach(btn => {
    btn.style.backgroundColor = "gray"
  })
  btn = document.getElementById("restart-btn")
  btn.style.backgroundColor = "blue"

  sendToServer("restart", id, type);
}

function stopVector(id, type) {  status_buttons = document.querySelectorAll(".status_button")
  status_buttons.forEach(btn => {
    btn.style.backgroundColor = "gray"
  })
  btn = document.getElementById("stop-btn")
  btn.style.backgroundColor = "yellow"

  sendToServer("stop", id, type);
}

function updateVector(id, type) {
  status_buttons = document.querySelectorAll(".status_button")
  status_buttons.forEach(btn => {
    btn.style.backgroundColor = "gray"
  })
  btn = document.getElementById("update-btn")
  btn.style.backgroundColor = "orange"

  showForm(type, id);
}

function deleteVector(id, type) {
  status_buttons = document.querySelectorAll(".status_button")
  status_buttons.forEach(btn => {
    btn.style.backgroundColor = "gray"
  })
  btn = document.getElementById("delete-btn")
  btn.style.backgroundColor = "red"

  sendToServer("delete", id, type);
}

function sendToServer(action, id, type) {
  const payload = {
    action,
    type,
    id,
    vector_name: `${type}_vector_${id}`,
    timestamp: new Date().toISOString(),
    client: "frontend-ui",
    status: "pending",
    data: vectors[id].data
  };

  fetch("http://localhost:5000/vector-action", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  })
    .then(res => res.json())
    .then(res => console.log(`✅ Server response:`, res))
    .catch(err => console.error("❌ Error sending to server:", err));
}
