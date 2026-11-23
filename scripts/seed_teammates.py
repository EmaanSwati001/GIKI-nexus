"""
Seed script for GIKI Nexus Teammate Finder database.
Populates realistic student profiles and collaborative capstone/research projects.
"""

from backend.app.database.session import SessionLocal, init_db
from backend.app.models.teammates import (
    StudentProfile,
    Project,
    ProjectMember,
    ProfileVisibility,
    ContactPreference,
    ProjectStatus,
    generate_ownership_key,
)

SAMPLE_PROFILES = [
    {
        "id": "std_ali_khan",
        "display_name": "Ali Khan",
        "email": "ali.khan.cs22@giki.edu.pk",
        "programme": "BS Computer Science",
        "academic_year": 3,
        "technical_skills": ["Python", "PyTorch", "FastAPI", "React", "Docker"],
        "research_interests": ["Deep Learning", "Computer Vision", "Autonomous Systems"],
        "preferred_domains": ["Artificial Intelligence", "Robotics"],
        "preferred_roles": ["ML Engineer", "Backend Developer"],
        "availability": "15 hrs/week",
        "previous_experience": "Built autonomous lane detection model for GIKI Robotics Club. Finalist at IEEE RoboQuest 2024.",
        "bio": "Junior CS student passionate about applied AI and computer vision. Looking to build an impactful capstone project.",
        "project_ideas": "Autonomous drone navigation for campus security and delivery.",
        "visibility": ProfileVisibility.PUBLIC,
        "contact_preference": ContactPreference.UPON_REQUEST,
    },
    {
        "id": "std_fatima_zahra",
        "display_name": "Fatima Zahra",
        "email": "fatima.z.ai23@giki.edu.pk",
        "programme": "BS Artificial Intelligence",
        "academic_year": 2,
        "technical_skills": ["Python", "TensorFlow", "Scikit-Learn", "SQL", "Data Analysis"],
        "research_interests": ["Natural Language Processing", "Healthcare AI", "Knowledge Graphs"],
        "preferred_domains": ["Bioinformatics", "Data Science"],
        "preferred_roles": ["Data Scientist", "NLP Researcher"],
        "availability": "10-12 hrs/week",
        "previous_experience": "Research intern at Data Science Lab, analyzed clinical datasets and published workshop paper.",
        "bio": "AI Sophomore interested in medical image segmentation and conversational agents for education.",
        "project_ideas": "Multilingual AI tutor for undergraduate STEM courses.",
        "visibility": ProfileVisibility.PUBLIC,
        "contact_preference": ContactPreference.OPEN,
    },
    {
        "id": "std_hamza_tariq",
        "display_name": "Hamza Tariq",
        "email": "hamza.t.ee21@giki.edu.pk",
        "programme": "BS Electrical Engineering",
        "academic_year": 4,
        "technical_skills": ["Embedded C", "C++", "ROS", "STM32", "PCB Design", "FPGA"],
        "research_interests": ["Embedded Systems", "Robotics", "IoT Hardware"],
        "preferred_domains": ["Robotics", "Hardware Engineering", "Cyber-Physical Systems"],
        "preferred_roles": ["Hardware Lead", "Embedded Systems Engineer"],
        "availability": "20 hrs/week",
        "previous_experience": "Team Lead for GIKI Shell Eco-marathon telemetry and motor control PCB design.",
        "bio": "Final year EE student specializing in autonomous vehicle hardware and real-time control loops.",
        "project_ideas": "Smart battery management system with IoT telemetry.",
        "visibility": ProfileVisibility.PUBLIC,
        "contact_preference": ContactPreference.UPON_REQUEST,
    },
    {
        "id": "std_sara_ahmed",
        "display_name": "Sara Ahmed",
        "email": "sara.ahmed.se22@giki.edu.pk",
        "programme": "BS Software Engineering",
        "academic_year": 3,
        "technical_skills": ["TypeScript", "Next.js", "Tailwind CSS", "Node.js", "GraphQL", "UI/UX Design"],
        "research_interests": ["Human-Computer Interaction", "Distributed Systems", "Web Performance"],
        "preferred_domains": ["Web Development", "Cloud Architecture", "Mobile Apps"],
        "preferred_roles": ["Frontend Lead", "Full-Stack Developer", "UI/UX Designer"],
        "availability": "12 hrs/week",
        "previous_experience": "Developed web portals for 3 GIKI annual student societies and GDSC hackathon winner.",
        "bio": "Full-stack enthusiast focused on clean software architecture and intuitive design systems.",
        "project_ideas": "Peer collaboration and course note verification platform.",
        "visibility": ProfileVisibility.PUBLIC,
        "contact_preference": ContactPreference.OPEN,
    },
    {
        "id": "std_bilal_hassan",
        "display_name": "Bilal Hassan",
        "email": "bilal.h.me22@giki.edu.pk",
        "programme": "BS Mechanical Engineering",
        "academic_year": 3,
        "technical_skills": ["SolidWorks", "ANSYS", "MATLAB", "Computational Fluid Dynamics", "CAD/CAM"],
        "research_interests": ["Aerodynamics", "Thermal Engineering", "Robotic Actuators"],
        "preferred_domains": ["Mechanical Design", "Renewable Energy", "Aerospace"],
        "preferred_roles": ["Mechanical Design Lead", "Simulation Engineer"],
        "availability": "15 hrs/week",
        "previous_experience": "Chassis and suspension design for GIKI Formula Student racecar team.",
        "bio": "Mechanical engineering junior passionate about structural analysis, robotic mechanisms, and energy harvesting.",
        "project_ideas": "Hybrid wind-solar microturbine for remote monitoring stations.",
        "visibility": ProfileVisibility.PUBLIC,
        "contact_preference": ContactPreference.UPON_REQUEST,
    },
    {
        "id": "std_zainab_rehman",
        "display_name": "Zainab Rehman",
        "email": "zainab.r.cys23@giki.edu.pk",
        "programme": "BS Cyber Security",
        "academic_year": 2,
        "technical_skills": ["Linux", "Python", "Network Security", "Cryptography", "Wireshark", "Penetration Testing"],
        "research_interests": ["Network Defense", "Zero-Knowledge Proofs", "Secure IoT"],
        "preferred_domains": ["Cyber Security", "Blockchain"],
        "preferred_roles": ["Security Analyst", "Penetration Tester"],
        "availability": "10 hrs/week",
        "previous_experience": "Active player on Hack The Box (Top 5% Pakistan), GIKI Cyber Security Society member.",
        "bio": "Cyber Security student passionate about ethical hacking, defensive security, and firmware auditing.",
        "project_ideas": "Automated vulnerability scanner for campus smart devices.",
        "visibility": ProfileVisibility.PUBLIC,
        "contact_preference": ContactPreference.UPON_REQUEST,
    },
]

SAMPLE_PROJECTS = [
    {
        "id": "proj_campus_rover",
        "owner_id": "std_ali_khan",
        "title": "Autonomous Campus Security & Delivery Rover",
        "description": "Multi-disciplinary capstone project to build a four-wheel autonomous ground vehicle for autonomous perimeter mapping and package delivery across GIKI campus hills. Combines ROS2, SLAM, LiDAR obstacle avoidance, and computer vision object tracking.",
        "domains": ["Robotics", "Artificial Intelligence", "Embedded Systems"],
        "required_skills": ["ROS", "Python", "C++", "LiDAR", "SolidWorks"],
        "preferred_roles": ["Hardware Lead", "SLAM Algorithm Specialist", "Computer Vision Dev"],
        "additional_members_needed": 3,
        "status": ProjectStatus.OPEN,
    },
    {
        "id": "proj_giki_ai_tutor",
        "owner_id": "std_fatima_zahra",
        "title": "Explainable AI Course Companion & Knowledge Retrieval System",
        "description": "Building a Retrieval-Augmented Generation (RAG) platform grounded on GIKI course syllabi, verified lecture notes, and faculty research papers to give students accurate academic answers with citation links.",
        "domains": ["Artificial Intelligence", "Natural Language Processing", "Web Development"],
        "required_skills": ["Python", "FastAPI", "React", "Vector DB", "PyTorch"],
        "preferred_roles": ["Frontend Engineer", "Vector Database Lead", "ML Evaluation Specialist"],
        "additional_members_needed": 2,
        "status": ProjectStatus.OPEN,
    },
    {
        "id": "proj_smart_microgrid",
        "owner_id": "std_hamza_tariq",
        "title": "IoT-Enabled Campus Solar Microgrid Monitor & Load Balancer",
        "description": "Design of an intelligent energy management node that monitors rooftop solar panels on GIKI engineering blocks, forecasts power generation with edge ML, and dynamically sheds non-essential electrical loads during peak hours.",
        "domains": ["Renewable Energy", "Embedded Systems", "IoT"],
        "required_skills": ["Embedded C", "STM32", "MQTT", "Python", "PCB Design"],
        "preferred_roles": ["Firmware Developer", "Dashboard Developer", "Power Electronics Engineer"],
        "additional_members_needed": 2,
        "status": ProjectStatus.OPEN,
    },
    {
        "id": "proj_secure_peer_vault",
        "owner_id": "std_zainab_rehman",
        "title": "Decentralized Academic Credential & Past Paper Verification Vault",
        "description": "A zero-knowledge cryptographic protocol for students to publish and verify academic solutions, course evaluations, and project milestones without revealing private student identities or leaking exam material.",
        "domains": ["Cyber Security", "Cryptography", "Software Engineering"],
        "required_skills": ["Python", "Cryptography", "TypeScript", "Node.js"],
        "preferred_roles": ["Cryptographic Protocol Dev", "Full-Stack Dev"],
        "additional_members_needed": 2,
        "status": ProjectStatus.OPEN,
    },
]


def seed():
    init_db()
    db = SessionLocal()
    try:
        # Check if already seeded
        existing_count = db.query(StudentProfile).count()
        if existing_count > 0:
            print(f"Teammates DB already has {existing_count} student profiles.")
            return

        print("Seeding student profiles...")
        profiles_map = {}
        for pdata in SAMPLE_PROFILES:
            profile = StudentProfile(
                id=pdata["id"],
                display_name=pdata["display_name"],
                email=pdata["email"],
                programme=pdata["programme"],
                academic_year=pdata["academic_year"],
                technical_skills=pdata["technical_skills"],
                research_interests=pdata["research_interests"],
                preferred_domains=pdata["preferred_domains"],
                preferred_roles=pdata["preferred_roles"],
                availability=pdata["availability"],
                previous_experience=pdata.get("previous_experience"),
                bio=pdata.get("bio"),
                project_ideas=pdata.get("project_ideas"),
                visibility=pdata["visibility"],
                contact_preference=pdata["contact_preference"],
                is_active=True,
                ownership_key=generate_ownership_key(),
            )
            db.add(profile)
            profiles_map[pdata["id"]] = profile

        db.commit()

        print("Seeding projects...")
        for proj_data in SAMPLE_PROJECTS:
            project = Project(
                id=proj_data["id"],
                owner_id=proj_data["owner_id"],
                title=proj_data["title"],
                description=proj_data["description"],
                domains=proj_data["domains"],
                required_skills=proj_data["required_skills"],
                preferred_roles=proj_data["preferred_roles"],
                additional_members_needed=proj_data["additional_members_needed"],
                status=proj_data["status"],
                ownership_key=generate_ownership_key(),
            )
            db.add(project)

            # Add owner as initial project member
            member = ProjectMember(
                project_id=proj_data["id"],
                profile_id=proj_data["owner_id"],
                role="Project Lead / Creator",
            )
            db.add(member)

        db.commit()
        print(f"Successfully seeded {len(SAMPLE_PROFILES)} profiles and {len(SAMPLE_PROJECTS)} projects into teammates.db!")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
