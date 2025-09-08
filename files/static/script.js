// files/static/script.js

// Prevent browser from opening files when they are dropped onto the window
window.addEventListener('dragover', e => e.preventDefault());
window.addEventListener('drop', e => e.preventDefault());

// Ensure CSRF token is set from global variable or from form
function getCSRFToken() {
  return window.csrfToken || (document.querySelector('input[name="csrfmiddlewaretoken"]') && document.querySelector('input[name="csrfmiddlewaretoken"]').value) || '';
}

// Toggle visibility of a folder's file list and update icon
function toggleFolder(folderId) {
  const ul = document.getElementById(`folder-${folderId}`);
  const folderElem = ul ? ul.previousElementSibling : null;
  if (!ul) return;
  const isOpen = ul.style.display === 'block';
  ul.style.display = isOpen ? 'none' : 'block';
    if (folderElem && folderElem.tagName === 'STRONG') {
    // Only replace the arrow at the start
    folderElem.innerHTML = folderElem.innerHTML.replace(/^([▶️|▼])/, isOpen ? '▶️' : '▼');
  }
}

// Drag & drop handlers
let dragged = null;
function onDragStart(e) { dragged = e.target.dataset.fileId; }
function onDrop(e, folderId) {
  e.preventDefault();
  fetch('/move-file/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
    body: JSON.stringify({ file_id: dragged, folder_id: folderId })
  }).then(() => location.reload());
}

// Handle drag over (to allow drop)
function onDragOver(e) { e.preventDefault(); }

// Handle drag-and-drop upload into dropzone area
function handleDrop(e) {
  e.preventDefault();
  const form = document.querySelector('form[enctype]');
  const input = form.querySelector("input[type='file']");
  const dt = new DataTransfer();
  for (let i = 0; i < e.dataTransfer.files.length; i++) {
    dt.items.add(e.dataTransfer.files[i]);
  }
  input.files = dt.files;
  form.submit();
}

function handleFolderDrop(e, folderId) {
  e.preventDefault();
  const files = e.dataTransfer.files;
  if (!files || files.length === 0) return;
  const formData = new FormData();
  for (let i = 0; i < files.length; i++) {
    formData.append('files', files[i]);
  }
  // Optionally show a loading state
  const dropzone = document.querySelector('.dropzone-folder-upload[data-folder-id="' + folderId + '"]');
  if (dropzone) dropzone.innerHTML = '<span style="color:#1976d2;">Uploading...</span>';
  fetch(`/upload-to-folder/${folderId}/`, {
    method: 'POST',
    headers: { 'X-CSRFToken': getCSRFToken() },
    body: formData
  }).then(() => location.reload());
}

// Wait for DOM to be ready before attaching event listeners
window.addEventListener('DOMContentLoaded', function() {
  // Event delegation for all folder/file actions
  document.body.addEventListener('click', function(e) {
    // Folder toggle
    if (e.target.matches('strong[onclick^="toggleFolder"], strong[data-folder-id]')) {
      const folderId = e.target.getAttribute('data-folder-id') || (e.target.getAttribute('onclick') && e.target.getAttribute('onclick').match(/toggleFolder\('(.+?)'\)/)[1]);
      if (folderId) toggleFolder(folderId);
    }
    // Rename folder
    if (e.target.matches('button[onclick^="renameFolder"], button[data-rename-folder]')) {
      const folderId = e.target.getAttribute('data-rename-folder') || (e.target.getAttribute('onclick') && e.target.getAttribute('onclick').match(/renameFolder\('(.+?)'\)/)[1]);
      if (folderId) renameFolder(folderId);
    }
    // Delete folder
    if (e.target.matches('button[onclick^="deleteFolder"], button[data-delete-folder]')) {
      const folderId = e.target.getAttribute('data-delete-folder') || (e.target.getAttribute('onclick') && e.target.getAttribute('onclick').match(/deleteFolder\('(.+?)'\)/)[1]);
      if (folderId) deleteFolder(folderId);
    }
    // Delete file
    if (e.target.matches('button[onclick^="deleteFile"], button[data-delete-file]')) {
      const fileId = e.target.getAttribute('data-delete-file') || (e.target.getAttribute('onclick') && e.target.getAttribute('onclick').match(/deleteFile\('(.+?)'\)/)[1]);
      if (fileId) deleteFile(fileId);
    }
    // Copy file
    if (e.target.matches('button[onclick^="copyFile"], button[data-copy-file]')) {
      const fileId = e.target.getAttribute('data-copy-file') || (e.target.getAttribute('onclick') && e.target.getAttribute('onclick').match(/copyFile\('(.+?)'\)/)[1]);
      if (fileId) {
        // Show folder picker modal for copy
        fetch('/folder-list-json/')
          .then(resp => resp.json())
          .then(folders => {
            let options = folders.map(f => `<option value="${f.id}">${f.name}</option>`).join('');
            let html = `<div id='copy-modal' style='position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(0,0,0,0.18);z-index:9999;display:flex;align-items:center;justify-content:center;'>
              <div style='background:#fff;padding:1.5em 2em;border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,0.15);min-width:260px;'>
                <div style='margin-bottom:1em;'>Copy file to folder:</div>
                <select id='copy-folder-select' style='width:100%;margin-bottom:1em;'>${options}</select>
                <button id='copy-confirm-btn' style='margin-right:0.7em;'>Copy</button>
                <button id='copy-cancel-btn'>Cancel</button>
              </div>
            </div>`;
            document.body.insertAdjacentHTML('beforeend', html);
            document.getElementById('copy-cancel-btn').onclick = function() {
              document.getElementById('copy-modal').remove();
            };
            document.getElementById('copy-confirm-btn').onclick = function() {
              const folderId = document.getElementById('copy-folder-select').value;
              fetch('/copy-file/', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ file_id: fileId, folder_id: folderId })
              }).then(() => location.reload());
            };
          });
      }
    }
    // Move file
    if (e.target.matches('button[onclick^="moveFilePrompt"], button[data-move-file]')) {
      const fileId = e.target.getAttribute('data-move-file') || (e.target.getAttribute('onclick') && e.target.getAttribute('onclick').match(/moveFilePrompt\('(.+?)'\)/)[1]);
      if (fileId) moveFilePrompt(fileId);
    }
    // Select All checkbox
    if (e.target.matches('.select-all-files')) {
      const folderId = e.target.getAttribute('data-folder-id');
      const checkboxes = document.querySelectorAll('.file-checkbox[data-folder-id="' + folderId + '"]');
      for (const cb of checkboxes) {
        cb.checked = e.target.checked;
      }
    }
    // Delete selected files in a folder
    if (e.target.matches('.delete-selected-btn')) {
      const folderId = e.target.getAttribute('data-folder-id');
      const fileIds = getSelectedFileIds(folderId);
      if (fileIds.length === 0) {
        alert('No files selected.');
        return;
      }
      if (!confirm('Delete selected files?')) return;
      fetch('/delete-multiple-files/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({ file_ids: fileIds })
      }).then(response => {
        if (!response.ok) alert('Delete failed');
        location.reload();
      }).catch(err => alert('Delete error: ' + err));
    }
  });

  // Folder list click handler for dashboard layout
  const folderListPanel = document.getElementById('folder-list-panel');
  const folderDetailPanel = document.getElementById('folder-detail-panel');
  if (folderListPanel && folderDetailPanel) {
    folderListPanel.addEventListener('click', function(e) {
      const item = e.target.closest('.folder-list-item');
      if (!item) return;
      // Highlight selected
      folderListPanel.querySelectorAll('.folder-list-item').forEach(el => el.classList.remove('selected'));
      item.classList.add('selected');
      // Fetch folder details
      const folderId = item.getAttribute('data-folder-id');
      fetch(`/folder-detail/${folderId}/`)
        .then(resp => resp.text())
        .then(html => {
          folderDetailPanel.innerHTML = html;
          // Re-attach dropzone listeners to the newly loaded content
          const newDropzone = folderDetailPanel.querySelector('.dropzone-folder-upload');
          if (newDropzone) {
            attachDropzoneListeners(newDropzone);
          }
        })
        .catch(() => {
          folderDetailPanel.innerHTML = '<div style="color:#888;">Could not load folder details.</div>';
        });
    });
  }

  // Move selected files to folder
  document.body.addEventListener('click', function(e) {
    if (e.target.matches('.move-selected-btn')) {
      const folderId = e.target.getAttribute('data-folder-id');
      const fileIds = getSelectedFileIds(folderId);
      if (fileIds.length === 0) {
        alert('No files selected.');
        return;
      }
      fetch('/folder-list-json/')
        .then(resp => resp.json())
        .then(folders => {
          let options = folders.map(f => `<option value="${f.id}">${f.name}</option>`).join('');
          let html = `<div id='move-modal' style='position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(0,0,0,0.18);z-index:9999;display:flex;align-items:center;justify-content:center;'>
            <div style='background:#fff;padding:1.5em 2em;border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,0.15);min-width:260px;'>
              <div style='margin-bottom:1em;'>Move selected files to folder:</div>
              <select id='move-folder-select' style='width:100%;margin-bottom:1em;'>${options}</select>
              <button id='move-confirm-btn' style='margin-right:0.7em;'>Move</button>
              <button id='move-cancel-btn'>Cancel</button>
            </div>
          </div>`;
          document.body.insertAdjacentHTML('beforeend', html);
          document.getElementById('move-cancel-btn').onclick = function() {
            document.getElementById('move-modal').remove();
          };
          document.getElementById('move-confirm-btn').onclick = function() {
            const targetFolderId = document.getElementById('move-folder-select').value;
            fetch('/move-multiple-files/', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
              },
              body: JSON.stringify({ file_ids: fileIds, folder_id: targetFolderId })
            }).then(() => location.reload());
          };
        });
    }
    // Copy selected files to folder
    if (e.target.matches('.copy-selected-btn')) {
      const folderId = e.target.getAttribute('data-folder-id');
      const fileIds = getSelectedFileIds(folderId);
      if (fileIds.length === 0) {
        alert('No files selected.');
        return;
      }
      fetch('/folder-list-json/')
        .then(resp => resp.json())
        .then(folders => {
          let options = folders.map(f => `<option value="${f.id}">${f.name}</option>`).join('');
          let html = `<div id='copy-modal' style='position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(0,0,0,0.18);z-index:9999;display:flex;align-items:center;justify-content:center;'>
            <div style='background:#fff;padding:1.5em 2em;border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,0.15);min-width:260px;'>
              <div style='margin-bottom:1em;'>Copy selected files to folder:</div>
              <select id='copy-folder-select' style='width:100%;margin-bottom:1em;'>${options}</select>
              <button id='copy-confirm-btn' style='margin-right:0.7em;'>Copy</button>
              <button id='copy-cancel-btn'>Cancel</button>
            </div>
          </div>`;
          document.body.insertAdjacentHTML('beforeend', html);
          document.getElementById('copy-cancel-btn').onclick = function() {
            document.getElementById('copy-modal').remove();
          };
          document.getElementById('copy-confirm-btn').onclick = function() {
            const targetFolderId = document.getElementById('copy-folder-select').value;
            fetch('/copy-multiple-files/', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
              },
              body: JSON.stringify({ file_ids: fileIds, folder_id: targetFolderId })
            }).then(() => location.reload());
          };
        });
    }
  });
});

// AJAX actions with error handling
function renameFolder(folderId) {
  const newName = prompt("Enter new folder name:");
  if (!newName) return;
  fetch('/rename-folder/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCSRFToken()
    },
    body: JSON.stringify({ folder_id: folderId, name: newName })
  }).then(response => {
    if (!response.ok) alert('Rename failed');
    location.reload();
  }).catch(err => alert('Rename error: ' + err));
}

function deleteFolder(folderId) {
  if (!confirm('Delete this folder and its contents?')) return;
  fetch('/delete-folder/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCSRFToken()
    },
    body: JSON.stringify({ folder_id: folderId })
  }).then(response => {
    if (!response.ok) alert('Delete failed');
    location.reload();
  }).catch(err => alert('Delete error: ' + err));
}

function deleteFile(fileId) {
  if (!confirm('Delete this file?')) return;
  fetch('/delete-file/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCSRFToken()
    },
    body: JSON.stringify({ file_id: fileId })
  }).then(response => {
    if (!response.ok) alert('Delete failed');
    location.reload();
  }).catch(err => alert('Delete error: ' + err));
}

// Utility: Get all selected file IDs (optionally for a specific folder)
function getSelectedFileIds(folderId = null) {
  const selector = folderId ? `.file-checkbox[data-folder-id="${folderId}"]` : '.file-checkbox';
  return Array.from(document.querySelectorAll(selector))
    .filter(cb => cb.checked)
    .map(cb => cb.getAttribute('data-file-id'));
}

// Function to attach listeners to a dropzone
function attachDropzoneListeners(dropzone) {
  dropzone.addEventListener('dragover', function(e) {
    e.preventDefault();
    this.classList.add('dragover');
  });
  dropzone.addEventListener('dragleave', function() {
    this.classList.remove('dragover');
  });
  dropzone.addEventListener('drop', function(e) {
  e.preventDefault();
    this.classList.remove('dragover');
    const folderId = this.getAttribute('data-folder-id');
    handleFolderDrop(e, folderId);
  });
}