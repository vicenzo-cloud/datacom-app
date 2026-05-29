// Carrega dados Chandon na aba Materiais

async function carregarChandonNoApp() {
  try {
    const response = await fetch('chandon_materiais.json');
    const dados = await response.json();

    if (!dados.materiais || dados.materiais.length === 0) return;

    // Adiciona aos materiais existentes
    adicionarMateriasChandon(dados);

    // Mostra análises
    mostrarAnaliseChandon(dados);

  } catch (error) {
    console.error('Erro ao carregar Chandon:', error);
  }
}

function adicionarMateriasChandon(dados) {
  // Procura pela tabela de materiais na aba Materiais
  const tabMateriais = document.querySelector('#page-projeto table.tbl tbody');

  if (!tabMateriais) return;

  // Adiciona cada material como linha
  dados.materiais.forEach((mat, idx) => {
    const tr = document.createElement('tr');

    let html = `
      <td>${mat.equipamento}</td>
      <td style="text-align:center">${mat.quantidade}</td>
      <td style="text-align:right">R$ ${mat.valor_unitario.toFixed(2)}</td>
      <td style="text-align:right">R$ ${mat.valor_total_previsto.toFixed(2)}</td>
      <td style="text-align:right">R$ ${mat.valor_total_real.toFixed(2)}</td>
      <td style="color:var(--blue)">${mat.marca}</td>
    `;

    tr.innerHTML = html;
    tr.style.backgroundColor = 'rgba(0, 212, 138, 0.05)';
    tabMateriais.appendChild(tr);
  });
}

function mostrarAnaliseChandon(dados) {
  // Procura o container de análises
  const pageProject = document.getElementById('page-projeto');
  if (!pageProject) return;

  const resumo = dados.resumo;

  // Cria card de análise
  const analyzeHTML = `
    <div class="card" style="margin-top: 20px; border-left: 4px solid var(--accent);">
      <div class="card-hd">
        <h3 class="card-title">Analise Chandon - ${dados.projeto}</h3>
      </div>

      <div class="metrics-row" style="margin-bottom: 16px;">
        <div class="mc green">
          <div class="mc-lbl">Total de Unidades</div>
          <div class="mc-val green">${resumo.total_unidades}</div>
        </div>
        <div class="mc blue">
          <div class="mc-lbl">Valor Previsto</div>
          <div class="mc-val blue">R$ ${resumo.valor_previsto.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
        </div>
        <div class="mc red">
          <div class="mc-lbl">Valor Real</div>
          <div class="mc-val red">R$ ${resumo.valor_real.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
        </div>
        <div class="mc ${resumo.diferenca < 0 ? 'red' : 'green'}">
          <div class="mc-lbl">Diferença</div>
          <div class="mc-val ${resumo.diferenca < 0 ? 'red' : 'green'}">R$ ${Math.abs(resumo.diferenca).toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
        </div>
      </div>

      <div class="note-box ${resumo.diferenca < 0 ? 'amber' : 'green'}" style="margin-top: 10px;">
        <span>${resumo.diferenca < 0 ? 'Custo acima do previsto' : 'Economia realizada'}: R$ ${Math.abs(resumo.diferenca).toLocaleString('pt-BR', {minimumFractionDigits: 2})} (${Math.abs(resumo.economia_percentual)}%)</span>
      </div>
    </div>
  `;

  // Insere no final da página
  pageProject.insertAdjacentHTML('beforeend', analyzeHTML);
}

// Carrega quando a aba Materiais é ativada
function setupChandonCarregamento() {
  const tabMateriais = document.getElementById('tab-materiais');
  if (tabMateriais) {
    tabMateriais.addEventListener('click', function() {
      setTimeout(carregarChandonNoApp, 200);
    });
  }
}

// Inicia quando DOM carrega
document.addEventListener('DOMContentLoaded', setupChandonCarregamento);
