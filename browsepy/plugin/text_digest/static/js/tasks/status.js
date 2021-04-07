/**
 *
 * @param brokerId {String}
 * @returns {HTMLTableRowElement|null}
 */
function getTaskRow(brokerId) {
  const rowId = `ct-${brokerId}`;
  return document.getElementById(rowId) || null;
}

/**
 *
 * @param row {HTMLTableRowElement}
 * @returns {HTMLButtonElement|null}
 */
function getTaskLoadBtn(row) {
  const cell = row.cells[3];
  return cell && cell.firstChild || null;
}

/**
 *
 * @param row {HTMLTableRowElement}
 * @returns {HTMLTableHeaderCellElement|null}
 */
function getTaskStatusCell(row) {
  return row.cells[1] || null;
}

/**
 *
 * @param row {HTMLTableRowElement}
 * @returns {HTMLTableHeaderCellElement|null}
 */
function getTaskResultCell(row) {
  return row.cells[4] || null;
}

/**
 *
 * @param brokerId {String}
 */
function disableTaskLoadBtn(brokerId) {
  const row = getTaskRow(brokerId);
  const btn = row && getTaskLoadBtn(row) || null;
  if (btn) { btn.disabled = true; }
}

/**
 *
 * @param brokerId {String}
 */
function enableTaskLoadBtn(brokerId) {
  const row = getTaskRow(brokerId);
  const btn = row && getTaskLoadBtn(row) || null;
  if (btn) { btn.disabled = false; }
}

/**
 *
 * @param brokerId {String}
 */
function registerFileTransformation(brokerId) {
  fetch(`/digest/cp/register/${brokerId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  })
    .then(response => {
    if (response.status === 201) {
      return response.json();
    } else if (response.status === 400) {
      fetchTaskStatus(brokerId);
    } else {
      throw new Error(response.statusText);
    }
  })
    .then(res => {
      console.log('File registered!', brokerId, res);
    })
    .catch(err => {
      console.error('Failed to register transformation', brokerId, err);
      enableTaskLoadBtn(brokerId);
    });
}

/**
 *
 * @param brokerId {String}
 */
function fetchTaskStatus(brokerId) {
  fetch(`/digest/task/${brokerId}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  })
    .then(response => {
      if (response.status === 200 || response.status === 404) {
        return response.json();
      } else {
        throw new Error(response.statusText);
      }
    })
    .then(res => {
      const {task_id, task_name, task_status, task_result,} = res.data;
      const taskRow = getTaskRow(brokerId);
      const statusCell = getTaskStatusCell(taskRow);
      const resultCell = getTaskResultCell(taskRow);
      if (statusCell) { statusCell.innerText = task_status; }
      switch (task_status) {
        case 'SUCCESS':
          console.log('Task complete!', task_id, task_name, task_status, task_result);
          if (resultCell) { resultCell.innerText = task_result; }
          registerFileTransformation(brokerId);
          break;
        case 'FAILED':
        case 'NOT FOUND':
          console.log('Task failed!', task_id, task_name, task_status, task_result);
          if (resultCell) { resultCell.innerText = 'No Result'; }
          break;
        default:
          console.log('Task pending.', task_id, task_name, task_status, task_result);
          if (resultCell) { resultCell.innerText = 'Pending'; }
          setTimeout(() => {
            console.log('Refreshing task status', task_id, task_name);
            fetchTaskStatus(task_id);
          }, 1_500);
        }
    })
    .catch(err => {
      console.error('Failed to fetch status', brokerId, err);
      enableTaskLoadBtn(brokerId);
    });
}

/**
 *
 * @param brokerId {String}
 */
function loadTaskStatus(brokerId) {
  disableTaskLoadBtn(brokerId);
  fetchTaskStatus(brokerId);
}
