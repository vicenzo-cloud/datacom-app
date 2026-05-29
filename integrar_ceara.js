// Integra dados Ceará (materiais) no projeto existente

async function integrarCearaMateriais() {
  try {
    const response = await fetch('ceara_materiais.json');
    const dados = await response.json();

    // Procura pelo projeto Ceará
    let projCeara = S.projects.find(p => p.id === 'b_print_cear');

    if (!projCeara) {
      // Se não existir, cria novo
      projCeara = {
        id: 'b_print_cear',
        nome: 'B_Print_Ceará',
        desc: 'Projeto com materiais e serviços',
        cliente: '',
        data: new Date().toISOString().split('T')[0],
        items: [],
        services: []
      };
      S.projects.push(projCeara);
    }

    // Limpa items antigos e adiciona novos
    projCeara.items = [];

    // Adiciona materiais do Ceará
    dados.materiais.forEach((mat, idx) => {
      const item = {
        id: mat.id,
        nome: mat.nome + ' (' + mat.marca + ')',
        cat: mat.categoria,
        prev: mat.valor_previsto,
        real: mat.valor_real,
        extra: false,
        qty: mat.quantidade
      };
      projCeara.items.push(item);
    });

    // Atualiza projeto selecionado
    S.proj = projCeara.id;

    // Recarrega interface
    renderAll();

    console.log('Ceará integrado com sucesso!');
    console.log('Materiais adicionados:', projCeara.items.length);
  } catch (error) {
    console.error('Erro ao integrar Ceará:', error);
  }
}

// Executa quando o app carrega
document.addEventListener('DOMContentLoaded', function() {
  setTimeout(integrarCearaMateriais, 500);
});
