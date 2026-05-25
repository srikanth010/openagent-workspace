#!/usr/bin/env python3
"""
MCP (Model Context Protocol) Server for Career Data
Implements JSON-RPC 2.0 over stdio with tool definitions for Srikanth's background.
"""

import json
import sys
import os
from pathlib import Path
from typing import Any, Optional

import yaml

# Data directory path (assumes this script is in apps/mcp/)
DATA_DIR = Path(__file__).parent.parent.parent / "data"

# Global state
CAREER_DATA = {}
PROJECTS_DATA = {}


def load_data():
    """Load career.yaml and projects.yaml at startup."""
    global CAREER_DATA, PROJECTS_DATA

    career_path = DATA_DIR / "career.yaml"
    projects_path = DATA_DIR / "projects.yaml"

    try:
        with open(career_path, 'r') as f:
            CAREER_DATA = yaml.safe_load(f) or {}
        log(f"Loaded career data from {career_path}")
    except FileNotFoundError:
        log(f"Warning: {career_path} not found")
        CAREER_DATA = {}

    try:
        with open(projects_path, 'r') as f:
            PROJECTS_DATA = yaml.safe_load(f) or {}
        log(f"Loaded projects data from {projects_path}")
    except FileNotFoundError:
        log(f"Warning: {projects_path} not found")
        PROJECTS_DATA = {}


def log(message: str):
    """Log to stderr so it doesn't corrupt the protocol stream."""
    print(f"[MCP] {message}", file=sys.stderr, flush=True)


def send_message(obj: dict):
    """Send a JSON-RPC message to stdout."""
    json.dump(obj, sys.stdout)
    sys.stdout.write('\n')
    sys.stdout.flush()


def read_message() -> Optional[dict]:
    """Read a JSON-RPC message from stdin."""
    try:
        line = sys.stdin.readline()
        if not line:
            return None
        return json.loads(line)
    except (json.JSONDecodeError, ValueError) as e:
        log(f"Error parsing JSON: {e}")
        return None


def handle_initialize(message: dict) -> dict:
    """Handle initialize request."""
    return {
        "jsonrpc": "2.0",
        "id": message.get("id"),
        "result": {
            "protocolVersion": "2024-11-05",
            "serverInfo": {
                "name": "srikanth-career-mcp",
                "version": "1.0.0"
            },
            "capabilities": {
                "tools": {}
            }
        }
    }


def get_tool_definitions() -> list:
    """Return MCP tool schema definitions."""
    return [
        {
            "name": "get_profile",
            "description": "Get Srikanth's professional profile and summary",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "list_skills",
            "description": "List Srikanth's technical and professional skills, optionally filtered by category",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Filter by skill category",
                        "enum": [
                            "ai_ml",
                            "systems_architecture",
                            "leadership",
                            "backend_languages",
                            "frontend_stack",
                            "infrastructure"
                        ]
                    }
                },
                "required": []
            }
        },
        {
            "name": "get_experience",
            "description": "Get Srikanth's work experience and roles, optionally filtered by company",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "company": {
                        "type": "string",
                        "description": "Company name to filter by (partial match)"
                    }
                },
                "required": []
            }
        },
        {
            "name": "get_projects",
            "description": "Get Srikanth's projects, optionally filtered by technology used",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "tech": {
                        "type": "string",
                        "description": "Technology to filter by (e.g., 'Python', 'React', 'FastAPI')"
                    }
                },
                "required": []
            }
        },
        {
            "name": "match_to_role",
            "description": "Match Srikanth's background to a job description. Returns fit score, relevant skills, and projects.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "job_description": {
                        "type": "string",
                        "description": "Job description or role summary to match against"
                    }
                },
                "required": ["job_description"]
            }
        }
    ]


def tool_get_profile() -> str:
    """Get profile information."""
    profile = CAREER_DATA.get("profile", {})
    return json.dumps({
        "name": profile.get("name"),
        "title": profile.get("title"),
        "summary": profile.get("summary"),
        "email": profile.get("email"),
        "github": profile.get("github"),
        "linkedin": profile.get("linkedin"),
        "website": profile.get("website"),
        "years_of_experience": profile.get("years_of_experience"),
        "location": profile.get("location")
    })


def tool_list_skills(category: Optional[str] = None) -> str:
    """List skills, optionally filtered by category."""
    skills = CAREER_DATA.get("skills", {})

    if category:
        category = category.lower()
        if category in skills:
            return json.dumps({
                category: skills[category]
            })
        else:
            return json.dumps({
                "error": f"Category '{category}' not found",
                "available_categories": list(skills.keys())
            })

    return json.dumps(skills)


def tool_get_experience(company: Optional[str] = None) -> str:
    """Get experience, optionally filtered by company."""
    experience = CAREER_DATA.get("experience", [])

    if company:
        company_lower = company.lower()
        filtered = [
            exp for exp in experience
            if company_lower in exp.get("company", "").lower()
        ]
        return json.dumps({
            "filtered_results": filtered,
            "total_count": len(filtered)
        })

    return json.dumps({
        "experience": experience,
        "total_count": len(experience)
    })


def tool_get_projects(tech: Optional[str] = None) -> str:
    """Get projects, optionally filtered by technology."""
    projects = PROJECTS_DATA.get("projects", [])

    if tech:
        tech_lower = tech.lower()
        filtered = [
            proj for proj in projects
            if any(tech_lower in t.lower() for t in proj.get("tech", []))
        ]
        return json.dumps({
            "filtered_results": filtered,
            "total_count": len(filtered)
        })

    return json.dumps({
        "projects": projects,
        "total_count": len(projects)
    })


def tool_match_to_role(job_description: str) -> str:
    """Match background to a job description using keyword scoring."""
    jd_lower = job_description.lower()

    # Extract keywords from job description
    keywords = set(jd_lower.split())

    skills = CAREER_DATA.get("skills", {})
    experience = CAREER_DATA.get("experience", [])
    projects = PROJECTS_DATA.get("projects", [])

    # Score skills
    skill_matches = []
    for category, skill_list in skills.items():
        for skill in skill_list:
            skill_lower = skill.lower()
            if any(kw in skill_lower for kw in keywords) or any(kw in skill_lower for kw in keywords):
                skill_matches.append({
                    "skill": skill,
                    "category": category
                })

    # Score projects
    project_matches = []
    for proj in projects:
        proj_tech = [t.lower() for t in proj.get("tech", [])]
        proj_desc = proj.get("description", "").lower()

        match_count = sum(1 for t in proj_tech if any(kw in t for kw in keywords))
        if match_count > 0 or any(kw in proj_desc for kw in keywords):
            project_matches.append({
                "name": proj.get("name"),
                "tech": proj.get("tech", []),
                "match_score": match_count
            })

    # Sort and limit
    skill_matches = skill_matches[:10]
    project_matches = sorted(project_matches, key=lambda x: x["match_score"], reverse=True)[:5]

    # Calculate overall fit score (0-100)
    fit_score = min(100, (len(skill_matches) + len(project_matches) * 2) * 5)

    return json.dumps({
        "job_summary": job_description[:200],
        "fit_score": fit_score,
        "relevant_skills": skill_matches,
        "relevant_projects": project_matches,
        "recommendation": (
            "Strong fit" if fit_score >= 70
            else "Good fit" if fit_score >= 50
            else "Moderate fit" if fit_score >= 30
            else "Needs more research"
        ),
        "summary": (
            f"Found {len(skill_matches)} relevant skills and {len(project_matches)} "
            f"relevant projects that align with this role."
        )
    })


def handle_tools_list(message: dict) -> dict:
    """Handle tools/list request."""
    return {
        "jsonrpc": "2.0",
        "id": message.get("id"),
        "result": {
            "tools": get_tool_definitions()
        }
    }


def handle_tools_call(message: dict) -> dict:
    """Handle tools/call request."""
    params = message.get("params", {})
    tool_name = params.get("name")
    arguments = params.get("arguments", {})

    try:
        if tool_name == "get_profile":
            result = tool_get_profile()
        elif tool_name == "list_skills":
            result = tool_list_skills(category=arguments.get("category"))
        elif tool_name == "get_experience":
            result = tool_get_experience(company=arguments.get("company"))
        elif tool_name == "get_projects":
            result = tool_get_projects(tech=arguments.get("tech"))
        elif tool_name == "match_to_role":
            result = tool_match_to_role(job_description=arguments.get("job_description", ""))
        else:
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {tool_name}"
                }
            }

        return {
            "jsonrpc": "2.0",
            "id": message.get("id"),
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": result
                    }
                ]
            }
        }
    except Exception as e:
        log(f"Error calling tool {tool_name}: {e}")
        return {
            "jsonrpc": "2.0",
            "id": message.get("id"),
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }


def main():
    """Main MCP server loop."""
    log("Starting MCP Career Server")
    load_data()
    log(f"Loaded {len(CAREER_DATA.get('experience', []))} experiences")
    log(f"Loaded {len(PROJECTS_DATA.get('projects', []))} projects")

    while True:
        message = read_message()
        if message is None:
            log("EOF received, shutting down")
            break

        method = message.get("method")

        try:
            if method == "initialize":
                response = handle_initialize(message)
            elif method == "notifications/initialized":
                # Notification, no response needed
                log("Client initialized")
                continue
            elif method == "tools/list":
                response = handle_tools_list(message)
            elif method == "tools/call":
                response = handle_tools_call(message)
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": message.get("id"),
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }

            send_message(response)
        except Exception as e:
            log(f"Error handling message: {e}")
            send_message({
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            })


if __name__ == "__main__":
    main()
