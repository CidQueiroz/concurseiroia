#!/bin/bash
echo "=========================================================="
echo "🌍 Iniciando o Túnel Seguro para a Internet (Pinggy)"
echo "=========================================================="
echo "Pinggy é muito mais estável para aplicativos como o Streamlit"
echo "pois não bloqueia o carregamento de scripts."
echo ""
echo "Aguarde conectar... Um link 'https' será exibido abaixo."
echo "Copie a URL que terminar com '.pinggy.link' e cole no seu celular!"
echo "----------------------------------------------------------"
echo "Para desligar o túnel quando voltar pra casa, aperte CTRL+C."
echo "----------------------------------------------------------"
ssh -p 443 -R0:localhost:8501 a.pinggy.io
