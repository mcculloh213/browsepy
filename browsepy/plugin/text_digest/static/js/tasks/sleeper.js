function handleClick(type) {
  fetch('/digest/task/sleeper', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ delay: type }),
  })
  .then(response => response.json())
  .then(res => getStatus(res.data.task_id));
}

function getTableRow(rowId, tableBodyId = 'data',
                     rowIdPrefix = 'data') {
  const dataId = `${rowIdPrefix}-${rowId}`;
  let row = rowId && document.getElementById(dataId);
  if (!row) {
    row = document.getElementById(tableBodyId).insertRow();
    row.id = dataId;
  }
  return row;
}

function getStatus(brokerId) {
  fetch(`/digest/task/${brokerId}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  })
  .then(response => response.json())
  .then(res => {
    const html = `<td>${brokerId}</td><td>${res.data.task_status}</td><td>${res.data.task_result}</td>`;
    const row = getTableRow(brokerId, 'tasks');
    row.innerHTML = html;
    const taskStatus = res.data.task_status;
    if (taskStatus === 'SUCCESS' || taskStatus === 'FAILED') return false;
    setTimeout(function() {
      getStatus(res.data.task_id);
    }, 1000);
  })
  .catch(err => console.log(err));
}
