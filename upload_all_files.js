#!/usr/bin/env node

import { Octokit } from '@octokit/rest';
import fs from 'fs';
import path from 'path';

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

async function getUncachableGitHubClient() {
  const accessToken = await getAccessToken();
  return new Octokit({ auth: accessToken });
}

// Función para leer archivos de forma recursiva
function getAllFiles(dirPath, arrayOfFiles = [], baseDir = dirPath) {
  const files = fs.readdirSync(dirPath);

  files.forEach(file => {
    const fullPath = path.join(dirPath, file);
    const stat = fs.statSync(fullPath);
    
    if (stat.isDirectory()) {
      // Ignorar directorios específicos
      const ignoreDirs = [
        '.git', 'node_modules', '.cache', '.upm', '.pythonlibs', 
        'temp', 'uploads', 'attached_assets', '__pycache__', 
        'frontend/node_modules', 'frontend/dist'
      ];
      
      const relativePath = path.relative(baseDir, fullPath);
      if (!ignoreDirs.some(dir => relativePath.includes(dir))) {
        getAllFiles(fullPath, arrayOfFiles, baseDir);
      }
    } else {
      // Ignorar archivos específicos
      const ignoreFiles = [
        '.replit', 'dump.rdb', 'celerybeat-schedule', 'generated-icon.png',
        'test_invoice.pdf', 'package-lock.json', 'uv.lock'
      ];
      
      const relativePath = path.relative(baseDir, fullPath);
      if (!ignoreFiles.some(ignore => relativePath.includes(ignore))) {
        arrayOfFiles.push({
          path: relativePath.replace(/\\/g, '/'), // Normalizar separadores
          fullPath: fullPath
        });
      }
    }
  });

  return arrayOfFiles;
}

// Función para subir un archivo via GitHub API
async function uploadFile(octokit, owner, repo, filePath, content, message) {
  try {
    const contentEncoded = Buffer.from(content).toString('base64');
    
    await octokit.rest.repos.createOrUpdateFileContents({
      owner: owner,
      repo: repo,
      path: filePath,
      message: message,
      content: contentEncoded,
      committer: {
        name: 'Sistema Ventas Paraguay',
        email: 'sistema@ventas.paraguay'
      },
      author: {
        name: 'Sistema Ventas Paraguay', 
        email: 'sistema@ventas.paraguay'
      }
    });
    
    console.log(`✅ Subido: ${filePath}`);
    return true;
  } catch (error) {
    console.error(`❌ Error subiendo ${filePath}:`, error.message);
    return false;
  }
}

async function main() {
  try {
    console.log('🚀 Iniciando subida completa del proyecto a GitHub...\n');
    
    const octokit = await getUncachableGitHubClient();
    const { data: user } = await octokit.rest.users.getAuthenticated();
    const owner = user.login;
    const repo = 'sistema-ventas-paraguay';
    
    console.log(`✅ Conectado como: ${owner}`);
    console.log(`📂 Repositorio objetivo: ${owner}/${repo}\n`);
    
    // Obtener todos los archivos
    console.log('📋 Recopilando archivos del proyecto...');
    const files = getAllFiles('.');
    
    console.log(`📁 Encontrados ${files.length} archivos para subir\n`);
    
    let uploaded = 0;
    let errors = 0;
    
    // Subir archivos principales primero
    const priorityFiles = files.filter(f => 
      f.path === 'README.md' || 
      f.path === 'replit.md' ||
      f.path === 'main.py' ||
      f.path === 'package.json' ||
      f.path === 'pyproject.toml'
    );
    
    console.log('📤 Subiendo archivos principales...');
    for (const file of priorityFiles) {
      const content = fs.readFileSync(file.fullPath, 'utf8');
      const success = await uploadFile(
        octokit, owner, repo, file.path, content,
        `Add ${file.path} - Sistema de gestión de ventas paraguayo`
      );
      
      if (success) uploaded++;
      else errors++;
      
      // Pequeña pausa para evitar rate limiting
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    // Subir el resto de archivos
    const remainingFiles = files.filter(f => !priorityFiles.includes(f));
    
    console.log('\n📤 Subiendo archivos restantes...');
    for (const file of remainingFiles) {
      try {
        const content = fs.readFileSync(file.fullPath, 'utf8');
        const success = await uploadFile(
          octokit, owner, repo, file.path, content,
          `Add project files - Sistema completo de ventas`
        );
        
        if (success) uploaded++;
        else errors++;
        
        // Pausa para evitar rate limiting
        await new Promise(resolve => setTimeout(resolve, 150));
        
      } catch (readError) {
        console.error(`❌ Error leyendo ${file.path}:`, readError.message);
        errors++;
      }
    }
    
    console.log('\n' + '='.repeat(50));
    console.log(`🎉 ¡Subida completada!`);
    console.log(`✅ Archivos subidos exitosamente: ${uploaded}`);
    console.log(`❌ Errores: ${errors}`);
    console.log(`📂 Repositorio: https://github.com/${owner}/${repo}`);
    console.log('='.repeat(50));
    
    if (uploaded > 0) {
      console.log('\n🇵🇾 ¡Sistema de gestión de ventas paraguayo subido a GitHub!');
      console.log('🔗 URL del repositorio: https://github.com/' + owner + '/' + repo);
    }
    
  } catch (error) {
    console.error('\n❌ Error general:', error.message);
    process.exit(1);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}