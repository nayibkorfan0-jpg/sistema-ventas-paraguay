#!/usr/bin/env node

import { Octokit } from '@octokit/rest';
import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';

let connectionSettings;

async function getAccessToken() {
  if (connectionSettings && connectionSettings.settings.expires_at && new Date(connectionSettings.settings.expires_at).getTime() > Date.now()) {
    return connectionSettings.settings.access_token;
  }
  
  const hostname = process.env.REPLIT_CONNECTORS_HOSTNAME
  const xReplitToken = process.env.REPL_IDENTITY 
    ? 'repl ' + process.env.REPL_IDENTITY 
    : process.env.WEB_REPL_RENEWAL 
    ? 'depl ' + process.env.WEB_REPL_RENEWAL 
    : null;

  if (!xReplitToken) {
    throw new Error('X_REPLIT_TOKEN not found for repl/depl');
  }

  connectionSettings = await fetch(
    'https://' + hostname + '/api/v2/connection?include_secrets=true&connector_names=github',
    {
      headers: {
        'Accept': 'application/json',
        'X_REPLIT_TOKEN': xReplitToken
      }
    }
  ).then(res => res.json()).then(data => data.items?.[0]);

  const accessToken = connectionSettings?.settings?.access_token || connectionSettings.settings?.oauth?.credentials?.access_token;

  if (!connectionSettings || !accessToken) {
    throw new Error('GitHub not connected');
  }
  return accessToken;
}

// WARNING: Never cache this client.
// Access tokens expire, so a new client must be created each time.
// Always call this function again to get a fresh client.
async function getUncachableGitHubClient() {
  const accessToken = await getAccessToken();
  return new Octokit({ auth: accessToken });
}

async function createGitHubRepository() {
  try {
    console.log('🔄 Connecting to GitHub...');
    const octokit = await getUncachableGitHubClient();
    
    // Get authenticated user
    const { data: user } = await octokit.rest.users.getAuthenticated();
    console.log(`✅ Connected as: ${user.login}`);
    
    const repoName = 'sistema-ventas-paraguay';
    const repoDescription = '🇵🇾 Sistema completo de gestión de ventas para empresas paraguayas con cumplimiento fiscal, régimen turístico, facturación IVA y más. FastAPI + React + PostgreSQL';
    
    console.log(`🔄 Creating repository: ${repoName}...`);
    
    // Create the repository
    const { data: repo } = await octokit.rest.repos.createForAuthenticatedUser({
      name: repoName,
      description: repoDescription,
      private: false, // Public repository
      auto_init: false, // We'll push our own content
      license_template: 'mit',
    });
    
    console.log(`✅ Repository created: ${repo.html_url}`);
    return repo;
    
  } catch (error) {
    if (error.status === 422) {
      console.log('ℹ️ Repository might already exist, continuing...');
      // Try to get the existing repository
      const octokit = await getUncachableGitHubClient();
      const { data: user } = await octokit.rest.users.getAuthenticated();
      const { data: repo } = await octokit.rest.repos.get({
        owner: user.login,
        repo: 'sistema-ventas-paraguay'
      });
      return repo;
    }
    throw error;
  }
}

async function setupGitAndPush(repo) {
  try {
    console.log('🔄 Setting up git configuration...');
    
    // Check if git is initialized
    if (!fs.existsSync('.git')) {
      execSync('git init', { stdio: 'inherit' });
    }
    
    // Configure git user (use GitHub info)
    const octokit = await getUncachableGitHubClient();
    const { data: user } = await octokit.rest.users.getAuthenticated();
    
    execSync(`git config user.name "${user.name || user.login}"`, { stdio: 'inherit' });
    execSync(`git config user.email "${user.email || user.login + '@users.noreply.github.com'}"`, { stdio: 'inherit' });
    
    // Add remote origin
    try {
      execSync(`git remote remove origin`, { stdio: 'ignore' });
    } catch (e) {
      // Remote might not exist, ignore
    }
    
    execSync(`git remote add origin ${repo.clone_url}`, { stdio: 'inherit' });
    
    console.log('🔄 Adding files to git...');
    execSync('git add .', { stdio: 'inherit' });
    
    console.log('🔄 Creating initial commit...');
    execSync('git commit -m "Initial commit: Sistema de gestión de ventas paraguayo\n\n🇵🇾 Sistema completo de gestión de ventas para empresas paraguayas\n- Backend FastAPI + SQLAlchemy + PostgreSQL\n- Frontend React + TypeScript + Vite\n- Cumplimiento fiscal paraguayo completo\n- Gestión de clientes con régimen turístico\n- Facturación con IVA y generación de PDFs\n- Dashboard y reportes integrados"', { stdio: 'inherit' });
    
    console.log('🔄 Pushing to GitHub...');
    execSync(`git push -u origin main`, { stdio: 'inherit' });
    
    console.log(`\n🎉 ¡Proyecto subido exitosamente a GitHub!`);
    console.log(`📂 Repositorio: ${repo.html_url}`);
    console.log(`🔗 Clone URL: ${repo.clone_url}`);
    
    return repo;
    
  } catch (error) {
    console.error('❌ Error durante la configuración de git o push:', error.message);
    throw error;
  }
}

async function main() {
  try {
    console.log('🚀 Iniciando subida del proyecto a GitHub...\n');
    
    // Create GitHub repository
    const repo = await createGitHubRepository();
    
    // Setup git and push
    await setupGitAndPush(repo);
    
    console.log('\n✅ ¡Proceso completado exitosamente!');
    console.log('\n📋 Detalles del repositorio:');
    console.log(`   Nombre: ${repo.name}`);
    console.log(`   URL: ${repo.html_url}`);
    console.log(`   Descripción: ${repo.description}`);
    console.log(`   Privado: ${repo.private ? 'Sí' : 'No'}`);
    
  } catch (error) {
    console.error('\n❌ Error:', error.message);
    process.exit(1);
  }
}

// Run if this is the main module
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}