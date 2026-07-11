ROLE_PROFILES = {
    "AI Engineer": {
        "title": "AI Engineer",
        "topics": ["Machine Learning", "Deep Learning", "Generative AI", "RAG (Retrieval-Augmented Generation)", "Fine-Tuning", "Vector Databases"],
        "description": "Focuses on designing and deploying AI systems, working with LLMs, prompt engineering, fine-tuning, and vector search engines.",
        "role_instructions": (
            "You are interviewing for an AI Engineer role. Ask questions covering core machine learning, deep learning, "
            "Large Language Models (LLMs), RAG systems, embedding techniques, and fine-tuning methodologies. "
            "Tailor your level of technical depth (e.g. asking about attention math, scaling limits, or framework code) based on the difficulty level."
        )
    },
    "Data Scientist": {
        "title": "Data Scientist",
        "topics": ["Statistics & Probability", "Machine Learning Algorithms", "Data Wrangling", "Feature Engineering", "A/B Testing", "Python/SQL"],
        "description": "Focuses on extracting insights from data, mathematical modeling, statistical analysis, and machine learning models.",
        "role_instructions": (
            "You are interviewing for a Data Scientist role. Focus your questions on statistics, probability, exploratory data analysis, "
            "supervised and unsupervised ML algorithms (regressions, trees, clustering), metric selection, model evaluation, and A/B testing design."
        )
    },
    "Backend Developer": {
        "title": "Backend Developer",
        "topics": ["API Design (REST/GraphQL)", "Database Schema Design & Query Tuning", "Caching (Redis)", "Concurrency & Multithreading", "System Design", "Security & Auth"],
        "description": "Focuses on server-side logic, database interactions, systems architecture, scalability, and performance optimization.",
        "role_instructions": (
            "You are interviewing for a Backend Developer role. Focus your questions on server-side architectures, REST/GraphQL API design, "
            "concurrency, database optimization, caching, microservices patterns, authentication mechanisms, and scaling bottlenecks."
        )
    },
    "Frontend Developer": {
        "title": "Frontend Developer",
        "topics": ["React / Next.js Core", "State Management (Redux/Zustand)", "DOM Performance & Rendering", "CSS Modules / Modern Layouts", "Browser APIs & Security", "Web Accessibility"],
        "description": "Focuses on user interfaces, client-side application logic, performance, and user experiences.",
        "role_instructions": (
            "You are interviewing for a Frontend Developer role. Focus your questions on client-side frameworks (specifically React/Next.js), "
            "DOM optimization, state management architectures, rendering strategies (SSR, SSG, Hydration), browser security principles (CORS, XSS), and CSS layouts."
        )
    },
    "Full Stack Developer": {
        "title": "Full Stack Developer",
        "topics": ["Frontend Integration", "Backend APIs", "Database Relationships", "Deployment & CI/CD", "State Management", "System Architecture"],
        "description": "Focuses on both client-side and server-side components, end-to-end features, and integration.",
        "role_instructions": (
            "You are interviewing for a Full Stack Developer role. Your questions should bridge client-side and server-side engineering. "
            "Ask about API consumption, full-stack state coordination, system design, database integration, and security across the entire web stack."
        )
    }
}
