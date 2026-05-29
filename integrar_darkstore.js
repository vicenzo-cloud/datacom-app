// Integra dados DarkStore (materiais) no projeto existente

async function integrarDarkstoreMateriais() {
  try {
    const response = await fetch('darkstore_materiais.json');
    const dados = await response.json();

    // Procura pelo projeto DarkStore existente
    let projDarkstore = S.projects.find(p => p.id === 'darkstore');

    if (projDarkstore) {
      // Limpa items antigos e adiciona novos
      projDarkstore.items = [];

    // Adiciona materiais do DarkStore
    dados.materiais.forEach((mat, idx) => {
      const item = {
        id: mat.id,
        nome: mat.nome + ' (' + mat.marca + ')',
        cat: 'Equipment',
        prev: mat.valor_previsto,
        real: mat.valor_real,
        extra: false,
        qty: mat.quantidade
      };
      projDarkstore.items.push(item);
    });

      // Atualiza projeto selecionado
      S.proj = projDarkstore.id;

      // Recarrega interface
      renderAll();

      console.log('DarkStore integrado com sucesso!');
      console.log('Materiais adicionados:', projDarkstore.items.length);
    } else {
      console.warn('Projeto DarkStore não encontrado no sistema');
    }
  } catch (error) {
    console.error('Erro ao integrar DarkStore:', error);
  }
}

// Executa quando o app carrega
document.addEventListener('DOMContentLoaded', function() {
  setTimeout(integrarDarkstoreMateriais, 500);
});
