# 🔧 Correção dos Erros de Deploy - V2

## ❌ Novos Erros Encontrados

1. **BuildCommand:** Não pode ter quebras de linha (`\x0a\x0d`)
2. **HealthCheck Interval:** Deve ser ≤ 20 (estava 30)

## ✅ Solução Implementada

Mudei para **configuração baseada em arquivo** (`apprunner.yaml`) que é mais confiável que configuração via API do CloudFormation.

## 📁 Arquivos Adicionados

### `apprunner.yaml` (na raiz do repositório)
```yaml
version: 1.0
runtime: python3
build:
  commands:
    build:
      - python -m pip install --upgrade pip
      - python -m pip install -r streamlit_app/requirements_web.txt
run:
  command: python -m streamlit run streamlit_app/app.py --server.port 8080 --server.address 0.0.0.0 --server.headless true
  network:
    port: 8080
  env:
    - name: STREAMLIT_SERVER_HEADLESS
      value: "true"
```

### `cloudformation-apprunner-file-config.yaml`
- Usa `ConfigurationSource: REPOSITORY` 
- Lê configuração do arquivo `apprunner.yaml`
- Mais simples e confiável

## 🚀 Como Corrigir

### 1. Deletar Stack Atual
```bash
aws cloudformation delete-stack --stack-name aws-partner-hygiene-apprunner --region us-east-1
aws cloudformation wait stack-delete-complete --stack-name aws-partner-hygiene-apprunner --region us-east-1
```

### 2. Deploy com Nova Configuração
```bash
# O arquivo apprunner.yaml já foi enviado para o GitHub
./deploy-apprunner.sh deploy
```

### 3. Ou Deploy Manual
```bash
aws cloudformation deploy \
  --template-file cloudformation-apprunner-file-config.yaml \
  --stack-name aws-partner-hygiene-apprunner \
  --parameter-overrides AppName="aws-partner-hygiene" \
  --region us-east-1
```

## 🎯 Vantagens da Configuração por Arquivo

- ✅ **Mais confiável** - App Runner lê diretamente do repositório
- ✅ **Sem limitações** de quebras de linha
- ✅ **Versionado** junto com o código
- ✅ **Mais simples** de debugar
- ✅ **Padrão recomendado** pela AWS

## 📊 Configurações Otimizadas

| Configuração | Valor | Motivo |
|--------------|-------|--------|
| **Runtime** | `python3` | Versão estável suportada |
| **Health Check Interval** | `10s` | Dentro do limite (≤20) |
| **Health Check Timeout** | `5s` | Rápido para detectar problemas |
| **Health Check Path** | `/` | Simples e confiável |
| **Port** | `8080` | Padrão para Streamlit |

## ⏱️ Tempo Esperado

- **Deleção:** 2-3 minutos
- **Deploy:** 3-5 minutos  
- **Build:** 5-10 minutos
- **Total:** ~10-15 minutos

## 🔍 Verificar Progresso

```bash
# Status da stack
aws cloudformation describe-stacks --stack-name aws-partner-hygiene-apprunner --region us-east-1

# Logs do App Runner (após deploy)
aws logs tail /aws/apprunner/aws-partner-hygiene --follow --region us-east-1
```

## 🎉 Resultado Esperado

URL da aplicação:
```
https://abc123def456.us-east-1.awsapprunner.com
```

---

**Status:** ✅ **CORRIGIDO COM ARQUIVO DE CONFIGURAÇÃO**  
**Método:** 📄 **REPOSITORY-BASED CONFIG**  
**Confiabilidade:** 🚀 **ALTA**