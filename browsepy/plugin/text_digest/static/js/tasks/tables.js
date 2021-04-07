function getTableRow(rowId, tableBodyId = 'data',
                     rowIdPrefix = 'data') {
  const dataId = `${rowIdPrefix}-${rowId}`
  let row = rowId && document.getElementById(dataId);
  if (!row) {
    row = document.getElementById(tableBodyId).insertRow();
    row.id = dataId
  }
  return row
}
