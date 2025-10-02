# 🚀 Deploy Guide - AWS Console

## 📁 Arquivo para Deploy

**Use este arquivo:** `cloudformation-deploy.yaml`

## 🎯 Deploy via AWS Console

### 1. Acessar CloudFormation
- Vá para: https://console.aws.amazon.com/cloudformation/
- Região: **us-east-1** (ou sua região preferida)

### 2. Criar Stack
1. Clique **"Create stack"** → **"With new resources"**
2. **Template source:** Upload a template file
3. **Choose file:** Selecione `cloudformation-deploy.yaml`
4. Clique **"Next"**

### 3. Configurar Stack
- **Stack name:** `aws-partner-hygiene-app`
- **AppName:** `aws-partner-hygiene` (ou mantenha padrão)
- Clique **"Next"**

### 4. Opções da Stack
- Mantenha padrões
- Clique **"Next"**

### 5. Review e Deploy
- Revise configurações
- Clique **"Submit"**

## ⏱️ Tempo de Deploy

- **Stack creation:** 5-10 minutos
- **App build:** 5-10 minutos
- **Total:** 10-20 minutos

## 📊 Monitorar Progresso

### CloudFormation Console
- Aba **"Events"** - mostra progresso da stack
- Aba **"Resources"** - mostra recursos criados

### App Runner Console
1. Vá para: https://console.aws.amazon.com/apprunner/
2. Selecione seu serviço
3. Aba **"Logs"** → **"Deployment logs"**

## 🎉 Após Deploy Bem-sucedido

### Obter URL da Aplicação
1. CloudFormation Console
2. Sua stack → Aba **"Outputs"**
3. Copie o valor de **"AppRunnerServiceUrl"**

### Testar Aplicação
- Acesse a URL fornecida
- Aguarde carregar (pode demorar alguns segundos)
- Faça upload de um arquivo Excel para testar

## 🔧 Se Houver Problemas

### Build Falha
1. App Runner Console → Logs → Deployment logs
2. Procure por erros de instalação de dependências
3. Se necessário, delete a stack e tente novamente

### Aplicação Não Carrega
1. Verifique se health check está passando
2. Aguarde mais alguns minutos (pode demorar)
3. Verifique logs de runtime no App Runner

### Delete Stack (se necessário)
1. CloudFormation Console
2. Selecione sua stack
3. **"Delete"** → Confirme

## 💰 Custo Estimado

- **App Runner:** ~$30-50/mês (0.5 vCPU, 1 GB)
- **Sem uso:** ~$0 (pay-per-use)

## 🔄 Atualizações

Para atualizar a aplicação:
1. Faça push de mudanças para GitHub
2. App Runner Console → **"Deploy"** → **"Manual deployment"**

---

**Arquivo principal:** ✅ `cloudformation-deploy.yaml`  
**Tempo total:** ⏱️ 10-20 minutos  
**Custo:** 💰 ~$30-50/mês