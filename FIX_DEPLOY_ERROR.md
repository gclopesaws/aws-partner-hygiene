# 🔧 Correção do Erro de Deploy

## ❌ Erro Encontrado
```
PYTHON_3_11 is not a valid enum value
```

## ✅ Correção Aplicada

O App Runner não suporta `PYTHON_3_11`, apenas `PYTHON_3`. Criei uma versão corrigida e simplificada.

## 🚀 Como Corrigir

### Opção 1: Deletar Stack e Recriar (RECOMENDADO)

```bash
# 1. Deletar stack com erro
aws cloudformation delete-stack --stack-name aws-partner-hygiene-apprunner --region us-east-1

# 2. Aguardar deleção completa (2-3 minutos)
aws cloudformation wait stack-delete-complete --stack-name aws-partner-hygiene-apprunner --region us-east-1

# 3. Deploy com template corrigido
./deploy-apprunner.sh deploy
```

### Opção 2: Deploy Manual com Template Simplificado

```bash
aws cloudformation deploy \
  --template-file cloudformation-apprunner-simple.yaml \
  --stack-name aws-partner-hygiene-apprunner-v2 \
  --parameter-overrides AppName="aws-partner-hygiene" \
  --region us-east-1 \
  --no-fail-on-empty-changeset
```

## 📋 Principais Correções Feitas

1. **Runtime:** `PYTHON_3_11` → `PYTHON_3`
2. **Build Command:** Usar `python -m pip` em vez de `pip`
3. **Start Command:** Usar `python -m streamlit` em vez de `streamlit`
4. **Health Check:** Simplificado para usar `/` em vez de `/_stcore/health`
5. **Template:** Removido IAM roles desnecessários para simplificar

## 🎯 Template Simplificado

O novo template `cloudformation-apprunner-simple.yaml` é mais robusto:

- ✅ **Runtime correto:** `PYTHON_3`
- ✅ **Comandos otimizados** para App Runner
- ✅ **Health check simples** e confiável
- ✅ **Menos recursos** = menos pontos de falha
- ✅ **Deploy mais rápido**

## 🔍 Verificar Status

```bash
# Verificar se stack antiga foi deletada
aws cloudformation describe-stacks --stack-name aws-partner-hygiene-apprunner --region us-east-1

# Se retornar erro "does not exist", pode prosseguir com novo deploy
```

## 🚀 Novo Deploy

```bash
# Usar o script atualizado
./deploy-apprunner.sh deploy

# Ou manual
aws cloudformation deploy \
  --template-file cloudformation-apprunner-simple.yaml \
  --stack-name aws-partner-hygiene-apprunner \
  --parameter-overrides AppName="aws-partner-hygiene" \
  --region us-east-1
```

## ⏱️ Tempo Esperado

- **Deleção da stack:** 2-3 minutos
- **Novo deploy:** 5-10 minutos
- **Build da aplicação:** 5-10 minutos
- **Total:** ~15-20 minutos

## 🎉 Resultado Esperado

Após o deploy bem-sucedido, você receberá:
```
https://abc123def456.us-east-1.awsapprunner.com
```

---

**Status:** ✅ **CORRIGIDO**  
**Ação:** 🔄 **DELETAR E RECRIAR STACK**