"""Civil Service behaviour descriptors per grade.

Source: Success Profiles: Civil Service Behaviours (Cabinet Office, Jan 2025).
Used to inject grade-appropriate context into behaviour generation prompts.
"""

from __future__ import annotations

# Canonical behaviour names
BEHAVIOURS = [
    "Seeing the Big Picture",
    "Changing and Improving",
    "Making Effective Decisions",
    "Leadership",
    "Communicating and Influencing",
    "Working Together",
    "Developing Self and Others",
    "Managing a Quality Service",
    "Delivering at Pace",
]

# Definitions (grade-independent)
DEFINITIONS: dict[str, str] = {
    "Seeing the Big Picture": (
        "Understand how your role fits with and supports organisational objectives. "
        "Recognise the wider Civil Service priorities and ensure work is in the national interest."
    ),
    "Changing and Improving": (
        "Seek out opportunities to create effective change and suggest innovative ideas for improvement. "
        "Review ways of working, including seeking and providing feedback."
    ),
    "Making Effective Decisions": (
        "Use evidence and knowledge to support accurate, expert decisions and advice. "
        "Carefully consider alternative options, implications and risks of decisions."
    ),
    "Leadership": (
        "Show pride and passion for public service. Create and engage others in delivering a shared vision. "
        "Value difference, diversity and inclusion, ensuring fairness and opportunity for all."
    ),
    "Communicating and Influencing": (
        "Communicate purpose and direction with clarity, integrity and enthusiasm. "
        "Respect the needs, responses and opinions of others."
    ),
    "Working Together": (
        "Form effective partnerships and relationships with people both internally and externally, "
        "from a range of diverse backgrounds, sharing information, resources and support."
    ),
    "Developing Self and Others": (
        "Focus on continuous learning and development for self, others and the organisation as a whole."
    ),
    "Managing a Quality Service": (
        "Deliver service objectives with professional excellence, expertise and efficiency, "
        "taking account of diverse customer needs."
    ),
    "Delivering at Pace": (
        "Take responsibility for delivering timely and quality results with focus and drive."
    ),
}

# Grade-level descriptors: what is expected at each grade
# Format: { grade_key: { behaviour: [list of bullet descriptors] } }
GRADE_DESCRIPTORS: dict[str, dict[str, list[str]]] = {
    "EO": {
        "Seeing the Big Picture": [
            "understand how your work area contributes to the wider objectives of the department",
            "understand what your team is trying to achieve and how your role contributes to this",
            "be aware of how different parts of the organisation are related to each other",
            "understand the wider public-service environment you operate in",
        ],
        "Changing and Improving": [
            "find new ways of doing things, including using digital technology",
            "question why things are done in a certain way and make suggestions for improvements",
            "identify opportunities to do things differently and more effectively",
            "support colleagues to adapt to change",
        ],
        "Making Effective Decisions": [
            "recognise where you have the authority to make decisions",
            "ask for guidance from more experienced colleagues where needed",
            "seek out and consider information from multiple sources before making decisions",
            "respond constructively to ambiguous situations",
        ],
        "Leadership": [
            "set a good example for others by demonstrating Civil Service values",
            "take responsibility for your own actions and the actions of your team when asked",
            "be open and honest about your own performance and that of your team",
        ],
        "Communicating and Influencing": [
            "listen carefully and ask questions to check your understanding",
            "explain things clearly and in a way that others can understand",
            "use digital communications effectively",
            "adjust your style of communication to suit different audiences",
        ],
        "Working Together": [
            "be approachable, sensitive and supportive to colleagues",
            "build and maintain positive relationships within and beyond your team",
            "respect diversity and the unique qualities individuals bring",
            "communicate and collaborate across boundaries",
        ],
        "Developing Self and Others": [
            "take responsibility for your own learning and development",
            "seek out learning opportunities and reflect on experience",
            "share your knowledge and experience with others",
            "support colleagues who are new to the role or organisation",
        ],
        "Managing a Quality Service": [
            "identify and respond to the needs of your customers",
            "look for ways to improve the service you provide",
            "follow the right procedures and escalate issues when they arise",
            "take ownership of issues and follow them through to resolution",
        ],
        "Delivering at Pace": [
            "manage your time effectively, prioritising tasks appropriately",
            "take responsibility for the quality of your work",
            "be adaptable and flexible when priorities change",
            "work in a way that maximises the contribution of everyone in the team",
        ],
    },
    "HEO": {
        "Seeing the Big Picture": [
            "understand the strategic drivers for your area of work",
            "ensure your work and your team's work is in line with wider strategic priorities",
            "build knowledge of the wider public sector context",
            "engage with a broad set of stakeholders to inform your work",
        ],
        "Changing and Improving": [
            "use data and evidence to identify areas for improvement",
            "support the implementation of change in your area",
            "manage risks associated with change while encouraging innovation",
            "involve a diverse range of colleagues, stakeholders and delivery partners in developing suggestions for improvements",
        ],
        "Making Effective Decisions": [
            "understand the complexity and breadth of issues involved in a decision",
            "make effective use of evidence to inform decisions",
            "understand when to escalate decisions to more senior colleagues",
            "be transparent about the basis for your decisions",
        ],
        "Leadership": [
            "be a visible, confident leader who motivates and inspires others",
            "create a working environment where everyone can contribute",
            "tackle issues that affect team performance",
            "seek to understand and manage your own impact on others",
        ],
        "Communicating and Influencing": [
            "use a range of communication skills and tools to communicate effectively",
            "explain complex issues in a clear, concise and meaningful way",
            "negotiate and influence to achieve outcomes",
            "adapt your communication style to meet different needs",
        ],
        "Working Together": [
            "actively involve a broad range of views in your work",
            "ensure collaboration across boundaries",
            "resolve differences and manage conflict",
            "promote an environment where people feel they can raise concerns",
        ],
        "Developing Self and Others": [
            "take responsibility for the development of individuals in the team",
            "encourage a culture of continuous improvement and learning",
            "support colleagues to overcome challenges to their development",
            "create opportunities for colleagues to develop their skills",
        ],
        "Managing a Quality Service": [
            "understand the needs and expectations of a diverse range of customers",
            "identify and address issues affecting service quality",
            "plan resources and processes to deliver high-quality service",
            "identify improvements and manage risks to service delivery",
        ],
        "Delivering at Pace": [
            "show a positive approach to keeping the team's efforts focused on the top priorities",
            "ensure the most appropriate resources are available for colleagues",
            "regularly monitor your own and team's work against milestones",
            "act promptly to reassess workloads and priorities when there are conflicting demands",
        ],
    },
    "SEO": {
        "Seeing the Big Picture": [
            "understand the strategic drivers for your area of work",
            "ensure your work and your team's work is in line with wider strategic priorities",
            "build knowledge of the wider public sector context",
            "engage with a broad set of stakeholders to inform your work",
        ],
        "Changing and Improving": [
            "use data and evidence to identify areas for improvement",
            "support the implementation of change in your area",
            "manage risks associated with change while encouraging innovation",
            "involve a diverse range of colleagues, stakeholders and delivery partners in improving services",
        ],
        "Making Effective Decisions": [
            "analyse complex information to make well-founded recommendations",
            "take responsibility for decisions and their implementation",
            "understand when to escalate decisions to more senior colleagues",
            "balance innovation and risk in decision making",
        ],
        "Leadership": [
            "lead and develop individuals and teams to deliver outcomes",
            "create an inclusive culture where everyone can contribute",
            "challenge poor performance and promote high standards",
            "role model Civil Service values and behaviours",
        ],
        "Communicating and Influencing": [
            "communicate confidently and persuasively across a range of formats",
            "build credibility with a wide range of stakeholders",
            "use evidence and argument to influence others",
            "adapt style to different audiences and situations",
        ],
        "Working Together": [
            "build effective partnerships inside and outside your organisation",
            "foster a collaborative and inclusive working environment",
            "resolve conflict and manage difficult conversations",
            "champion diversity and inclusion in your team",
        ],
        "Developing Self and Others": [
            "champion continuous learning across your team",
            "provide constructive feedback and coaching to colleagues",
            "create development plans aligned to business needs",
            "model the learning culture you want to build in others",
        ],
        "Managing a Quality Service": [
            "ensure service delivery meets the needs of diverse customers",
            "proactively manage risks and issues affecting quality",
            "drive efficiency and continuous improvement",
            "engage stakeholders to improve service design and delivery",
        ],
        "Delivering at Pace": [
            "maintain focus and drive to deliver priorities on time",
            "empower others while retaining accountability for outcomes",
            "manage competing demands and adapt plans when needed",
            "foster a culture of pace, quality and accountability",
        ],
    },
    "Grade 7": {
        "Seeing the Big Picture": [
            "develop and maintain an understanding of economic, social, political, environmental and technological developments to ensure activity is relevant",
            "ensure plans and activities in your area of work reflect wider strategic priorities and communicate effectively with senior leaders to influence future strategies",
            "adopt a government-wide perspective to ensure alignment of activity and policy",
            "bring together views, perspectives and diverse needs of stakeholders to gain a broader understanding of the issues surrounding policies and activities",
        ],
        "Changing and Improving": [
            "encourage, recognise and share innovative ideas from a diverse range of colleagues and stakeholders",
            "give people space to take initiative and praise them for their creativity",
            "create an environment where people feel safe to challenge and know their voice will be heard",
            "make changes which add value and clearly articulate how changes will benefit the business",
            "understand and identify the role of technology in public service delivery and policy implementation",
            "consider the full impact of implementing changes on culture, structure, morale and the impacts on the diverse range of end users, including accessibility needs",
            "identify early signs that things are going wrong and respond promptly",
            "provide constructive challenge to senior management on change proposals",
        ],
        "Making Effective Decisions": [
            "clarify your own understanding and stakeholder needs and expectations, before making decisions",
            "ensure decision making happens at the right level, not allowing unnecessary bureaucracy to hinder delivery",
            "encourage both innovative suggestions and challenge from others, to inform decision making",
            "analyse and accurately interpret data from various sources to support decisions",
            "find the best option by identifying positives, negatives, risks and implications",
            "present reasonable conclusions from a wide range of complex and sometimes incomplete evidence",
            "make decisions confidently even when details are unclear or if they prove to be unpopular",
        ],
        "Leadership": [
            "promote diversity, inclusion and equality of opportunity, respecting difference and external experience",
            "welcome and respond to views and challenges from others, despite any conflicting pressures to ignore or give in to them",
            "stand by, promote or defend your own and your team's actions and decisions where needed",
            "seek out shared interests beyond your own area of responsibility, understanding the extent of the impact actions have on the organisation",
            "inspire and motivate teams to be fully engaged in their work and dedicated to their role",
        ],
        "Communicating and Influencing": [
            "communicate with others in a clear, honest and enthusiastic way in order to build trust",
            "explain complex issues in a way that is easy to understand",
            "take into account people's individual needs",
            "deliver difficult messages with clarity and sensitivity, being persuasive when required",
            "consider the impact of the language used",
            "remain open-minded and impartial in discussions, whilst respecting the diverse interests and opinions of others",
            "introduce different methods for communication, including making the most of digital resources whilst getting value for money",
            "monitor the effectiveness of own and team communications and take action to improve where necessary",
        ],
        "Working Together": [
            "actively build and maintain a network of colleagues and contacts to achieve progress on shared objectives",
            "challenge assumptions while being willing to compromise if beneficial to progress",
            "build strong interpersonal relationships and show genuine care for colleagues",
            "ensure consideration and support for the wellbeing of yourself and individuals throughout the team",
            "understand the varying needs of the team to ensure they are supported and their experiences are utilised",
            "create an inclusive working environment where all opinions and challenges are taken into account",
            "remain available and approachable to all colleagues and be receptive to new ideas",
        ],
        "Developing Self and Others": [
            "prioritise and role-model continuous self-learning and development",
            "identify areas individuals and teams need to develop in order to achieve future objectives",
            "support colleagues to take responsibility for their own learning and development",
            "ensure that development opportunities are available for all individuals regardless of their background or desire to achieve promotion",
            "ensure individuals take full advantage of learning and development opportunities available to them, including workplace-based learning",
            "encourage discussions within and between teams to learn from each other's experiences and change organisational plans and processes accordingly",
        ],
        "Managing a Quality Service": [
            "demonstrate positive customer service by understanding the complexity and diversity of customer needs and expectations",
            "deliver a high quality, efficient and cost-effective service by considering a broad range of methods for delivery",
            "ensure full consideration of new technologies, accessibility and costings",
            "make clear, practical and manageable plans for service delivery",
            "ensure adherence to legal, regulatory and security requirements in service delivery",
            "proactively manage risks and identify solutions",
            "establish how the business area compares to industry best practice",
            "create regular opportunities for colleagues, stakeholders, delivery partners and customers to help improve the quality of service",
        ],
        "Delivering at Pace": [
            "ensure everyone clearly understands and owns their roles, responsibilities and business priorities",
            "give honest, motivating and enthusiastic messages about priorities, objectives and expectations to get the best out of people",
            "comply with legal, regulatory and security requirements in service delivery",
            "set out clear processes and standards for managing performance at all levels",
            "ensure delivery of timely quality outcomes, through providing the right resources to do the job, reviewing and adjusting performance expectations and rewarding success",
            "maintain your own levels of performance in challenging circumstances and encourage others to do the same",
        ],
    },
    "Grade 6": {
        # Grade 6 shares descriptors with Grade 7
        "Seeing the Big Picture": [
            "develop and maintain an understanding of economic, social, political, environmental and technological developments",
            "ensure plans and activities in your area of work reflect wider strategic priorities",
            "adopt a government-wide perspective to ensure alignment of activity and policy",
            "bring together views, perspectives and diverse needs of stakeholders",
        ],
        "Changing and Improving": [
            "encourage and recognise innovative ideas from a diverse range of colleagues and stakeholders",
            "create an environment where people feel safe to challenge",
            "make changes which add value and clearly articulate how changes will benefit the business",
            "understand the role of technology in public service delivery",
            "provide constructive challenge to senior management on change proposals",
        ],
        "Making Effective Decisions": [
            "clarify stakeholder needs and expectations before making decisions",
            "analyse and accurately interpret data from various sources",
            "present reasonable conclusions from complex and sometimes incomplete evidence",
            "make decisions confidently even when details are unclear",
        ],
        "Leadership": [
            "promote diversity, inclusion and equality of opportunity",
            "inspire and motivate teams to be fully engaged in their work",
            "stand by your own and your team's actions and decisions where needed",
            "seek out shared interests beyond your own area of responsibility",
        ],
        "Communicating and Influencing": [
            "communicate with others in a clear, honest and enthusiastic way",
            "explain complex issues in a way that is easy to understand",
            "deliver difficult messages with clarity and sensitivity",
            "monitor the effectiveness of own and team communications",
        ],
        "Working Together": [
            "actively build and maintain a network of colleagues and contacts",
            "build strong interpersonal relationships and show genuine care for colleagues",
            "create an inclusive working environment where all opinions are taken into account",
        ],
        "Developing Self and Others": [
            "prioritise and role-model continuous self-learning and development",
            "identify development areas for individuals and teams",
            "support colleagues to take responsibility for their own learning",
        ],
        "Managing a Quality Service": [
            "deliver a high quality, efficient and cost-effective service",
            "proactively manage risks and identify solutions",
            "ensure adherence to legal, regulatory and security requirements",
        ],
        "Delivering at Pace": [
            "ensure everyone clearly understands and owns their roles and responsibilities",
            "ensure delivery of timely quality outcomes",
            "maintain your own levels of performance in challenging circumstances",
        ],
    },
}

# Grade aliases for common variations users might type
GRADE_ALIASES: dict[str, str] = {
    "g7": "Grade 7",
    "grade7": "Grade 7",
    "grade 7": "Grade 7",
    "g6": "Grade 6",
    "grade6": "Grade 6",
    "grade 6": "Grade 6",
    "seo": "SEO",
    "heo": "HEO",
    "eo": "EO",
    "ao": "AO",
    "aa": "AA",
}

ALL_GRADES = list(GRADE_DESCRIPTORS.keys())


def resolve_grade(grade: str) -> str | None:
    """Normalise a user-supplied grade string to a canonical key, or return None."""
    normalised = grade.strip().lower()
    # Exact match first
    for key in GRADE_DESCRIPTORS:
        if key.lower() == normalised:
            return key
    return GRADE_ALIASES.get(normalised)


def get_descriptors(grade: str, behaviour: str) -> list[str] | None:
    """Return bullet descriptors for a behaviour at a given grade, or None."""
    canonical_grade = resolve_grade(grade)
    if canonical_grade is None:
        return None
    grade_data = GRADE_DESCRIPTORS.get(canonical_grade, {})
    # Fuzzy match behaviour name
    for key, descriptors in grade_data.items():
        if key.lower() == behaviour.strip().lower():
            return descriptors
    # Partial match
    behaviour_lower = behaviour.strip().lower()
    for key, descriptors in grade_data.items():
        if behaviour_lower in key.lower() or key.lower() in behaviour_lower:
            return descriptors
    return None


def format_behaviour_context(grade: str, behaviour: str) -> str:
    """Return a formatted string of grade-specific behaviour descriptors for prompt injection."""
    definition = DEFINITIONS.get(behaviour, "")
    descriptors = get_descriptors(grade, behaviour)

    lines = [f"Behaviour: {behaviour}"]
    if definition:
        lines.append(f"Definition: {definition}")
    lines.append(f"Grade: {grade}")
    if descriptors:
        lines.append(f"At {grade} level, this behaviour means demonstrating:")
        for d in descriptors:
            lines.append(f"  • {d}")
    return "\n".join(lines)
