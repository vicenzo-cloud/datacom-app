// Integra dados Chandon (materiais + serviços) em um único projeto

async function integrarChandonUnificado() {
  try {
    const response = await fetch('chandon_materiais.json');
    const dados = await response.json();

    // Procura pelo projeto WiFi antigo
    const projWifi = S.projects.find(p => p.id === 'chandon_cameras_wifi');

    // Remove o projeto antigo se existir
    if (projWifi) {
      const idx = S.projects.indexOf(projWifi);
      if (idx > -1) {
        S.projects.splice(idx, 1);
      }
    }

    // Procura pelo projeto Chandon unificado
    let projChandon = S.projects.find(p => p.id === 'chandon-completo');

    if (!projChandon) {
      // Cria novo projeto unificado
      projChandon = {
        id: 'chandon-completo',
        nome: 'CHANDON - Câmeras Temporárias BoM',
        desc: 'Projeto unificado com materiais e serviços',
        cliente: 'Chandon',
        data: new Date().toISOString().split('T')[0],
        items: [],
        services: [],
        tab: 'materiais'
      };
      S.projects.push(projChandon);
    } else {
      // Limpa itens antigos se existir
      projChandon.items = [];
      projChandon.services = [];
    }

    // Adiciona materiais do Chandon
    dados.materiais.forEach((mat, idx) => {
      const item = {
        id: 'chd-mat-' + idx,
        nome: mat.equipamento + ' (' + mat.marca + ')',
        cat: mat.categoria,
        prev: mat.valor_total_previsto,
        real: mat.valor_total_real,
        extra: false,
        qty: mat.quantidade
      };
      projChandon.items.push(item);
    });

    // Adiciona serviços do projeto WiFi antigo
    if (projWifi && projWifi.services) {
      projWifi.services.forEach((svc, idx) => {
        const service = {
          id: 'chd-svc-' + idx,
          nome: svc.nome,
          qtd: svc.qtd,
          fornecedor: svc.fornecedor,
          prev: svc.prev,
          real: svc.real,
          cat: svc.cat || 'Serviço',
          extra: false
        };
        projChandon.services.push(service);
      });
    }

    // Atualiza o projeto selecionado
    S.proj = projChandon.id;

    // Recarrega interface
    renderAll();

    console.log('Chandon unificado com sucesso!');
    console.log('Materiais:', projChandon.items.length);
    console.log('Serviços:', projChandon.services.length);
  } catch (error) {
    console.error('Erro ao integrar Chandon:', error);
  }
}

// Executa quando o app carrega
document.addEventListener('DOMContentLoaded', function() {
  // Aguarda um pouco para garantir que S.projects foi carregado
  setTimeout(integrarChandonUnificado, 500);
});
