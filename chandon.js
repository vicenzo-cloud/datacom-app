// Integração Chandon - Câmeras Temporárias

async function loadChandonData() {
  try {
    const response = await fetch('dados_chandon.json');
    const data = await response.json();
    renderChandonTable(data.dados);
  } catch (error) {
    console.error('Erro ao carregar dados Chandon:', error);
    const tbody = document.getElementById('chandon-tbody');
    if (tbody) {
      tbody.innerHTML = '<tr><td colspan="100%">Erro ao carregar dados</td></tr>';
    }
  }
}

function renderChandonTable(dados) {
  if (!dados || dados.length === 0) {
    const tbody = document.getElementById('chandon-tbody');
    if (tbody) {
      tbody.innerHTML = '<tr><td colspan="100%">Nenhum dado disponível</td></tr>';
    }
    return;
  }

  // Cabeçalho
  const thead = document.getElementById('chandon-thead');
  if (thead) {
    const colunas = Object.keys(dados[0]);
    let headerHTML = '<tr>';
    colunas.forEach(col => {
      headerHTML += `<th>${col}</th>`;
    });
    headerHTML += '</tr>';
    thead.innerHTML = headerHTML;
  }

  // Corpo
  const tbody = document.getElementById('chandon-tbody');
  if (tbody) {
    const colunas = Object.keys(dados[0]);
    let bodyHTML = '';
    dados.forEach(row => {
      bodyHTML += '<tr>';
      colunas.forEach(col => {
        const valor = row[col] || '';
        bodyHTML += `<td>${valor}</td>`;
      });
      bodyHTML += '</tr>';
    });
    tbody.innerHTML = bodyHTML;
  }
}

function exportChandonData() {
  const table = document.getElementById('chandon-table');
  if (table && typeof XLSX !== 'undefined') {
    const wb = XLSX.utils.table_to_book(table);
    XLSX.writeFile(wb, 'Chandon_Dados.xlsx');
  } else {
    alert('Erro ao exportar dados');
  }
}

// Carrega dados quando a aba Chandon é clicada
function setupChandonTab() {
  const tabChandon = document.getElementById('tab-chandon');
  if (tabChandon) {
    tabChandon.addEventListener('click', function() {
      setTimeout(loadChandonData, 100);
    });
  }
}

// Inicializa quando o DOM carrega
document.addEventListener('DOMContentLoaded', setupChandonTab);
