"""GitHub publishing service"""
import base64
import json
from datetime import datetime
from typing import Dict, Any, Optional
import requests
import pytz
from config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)


class GitHubPublisher:
    """Service for publishing schema to GitHub repository"""
    
    def __init__(self):
        self.token = Config.GITHUB_TOKEN
        self.repo = Config.GITHUB_REPO
        self.file_path = Config.GITHUB_FILE_PATH
        self.base_url = Config.GITHUB_API_BASE
    
    async def get_current_file_sha(self) -> Optional[str]:
        """
        Get the current file SHA (required for GitHub API).
        
        Returns:
            File SHA if it exists, None if file doesn't exist
        """
        try:
            url = f"{self.base_url}/{self.repo}/contents/{self.file_path}"
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'DateSpot-Aggregator'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('sha')
            elif response.status_code == 404:
                logger.info("File doesn't exist yet, will create new")
                return None
            else:
                response.raise_for_status()
        
        except Exception as error:
            logger.error(f"Error getting file SHA: {error}")
            return None
    
    def prepare_function_code(self, schema: Dict[str, Any]) -> str:
        """
        Prepare the JavaScript function code for the schema.
        
        Args:
            schema: The schema data to embed
            
        Returns:
            JavaScript function code as string
        """
        function_code = f"""export default function handler(req, res) {{
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'X-API-Key, Content-Type');
  
  if (req.method === 'OPTIONS') {{
    return res.status(200).end();
  }}
  
  if (req.method !== 'GET') {{
    return res.status(405).json({{ error: 'Method not allowed' }});
  }}
  
  const apiKey = req.headers['x-api-key'];
  if (!apiKey || apiKey !== process.env.API_SECRET_KEY) {{
    return res.status(401).json({{ error: 'Unauthorized' }});
  }}
  
  const schema = {json.dumps(schema, indent=2)};
  
  res.setHeader('Cache-Control', 'public, max-age=3600');
  res.setHeader('Content-Type', 'application/json');
  
  return res.status(200).json(schema);
}}"""
        return function_code
    
    async def publish_to_github(self, schema: Dict[str, Any]) -> bool:
        """
        Publish the schema to GitHub repository.
        
        Args:
            schema: The schema data to publish
            
        Returns:
            True if successful, False otherwise
        """
        logger.info("Starting GitHub publication process...")
        
        try:
            # Get current file SHA
            logger.info("   🔍 Checking for existing file...")
            sha = await self.get_current_file_sha()
            
            if sha:
                logger.info(f"   ✓ Found existing file with SHA: {sha[:8]}...")
            else:
                logger.info("   ✓ No existing file found, will create new")
            
            # Prepare the new function code
            logger.info("   📝 Preparing JavaScript function code...")
            function_code = self.prepare_function_code(schema)
            logger.info(f"   📊 Function code size: {len(function_code)} characters")
            
            # Encode content as base64
            encoded_content = base64.b64encode(function_code.encode('utf-8')).decode('utf-8')
            
            # Prepare commit message with Toronto timezone
            toronto_tz = pytz.timezone('America/Toronto')
            toronto_time = datetime.now(toronto_tz)
            commit_message = f"Update schema from DateSpot Aggregator - {toronto_time.isoformat()}"
            
            # Prepare request payload
            payload = {
                'message': commit_message,
                'content': encoded_content
            }
            
            # Add SHA if file exists
            if sha:
                payload['sha'] = sha
            
            # Make GitHub API request
            url = f"{self.base_url}/{self.repo}/contents/{self.file_path}"
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Accept': 'application/vnd.github.v3+json',
                'Content-Type': 'application/json',
                'User-Agent': 'DateSpot-Aggregator'
            }
            
            logger.info(f"   🚀 Publishing to {self.repo}/{self.file_path}...")
            response = requests.put(
                url,
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            commit_sha = data.get('commit', {}).get('sha', 'unknown')
            logger.info(f"   ✓ Successfully published to GitHub")
            logger.info(f"   📊 Commit SHA: {commit_sha}")
            return True
        
        except Exception as error:
            logger.error(f"Error publishing to GitHub: {error}")
            return False
