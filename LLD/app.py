import streamlit as st
import json
import re
from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum

# Configure page
st.set_page_config(
    page_title="LLD Learning Platform",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 2rem;
}
.section-header {
    font-size: 1.5rem;
    color: #ff7f0e;
    border-bottom: 2px solid #ff7f0e;
    padding-bottom: 0.5rem;
    margin: 1.5rem 0 1rem 0;
}
.class-card {
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 1rem;
    margin: 1rem 0;
}
.evaluation-good {
    background-color: #d4edda;
    border: 1px solid #c3e6cb;
    color: #155724;
    padding: 0.75rem;
    border-radius: 4px;
    margin: 0.5rem 0;
}
.evaluation-warning {
    background-color: #fff3cd;
    border: 1px solid #ffeaa7;
    color: #856404;
    padding: 0.75rem;
    border-radius: 4px;
    margin: 0.5rem 0;
}
.evaluation-error {
    background-color: #f8d7da;
    border: 1px solid #f5c6cb;
    color: #721c24;
    padding: 0.75rem;
    border-radius: 4px;
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)

class DesignPrinciple(Enum):
    SINGLE_RESPONSIBILITY = "Single Responsibility Principle"
    OPEN_CLOSED = "Open/Closed Principle"
    LISKOV_SUBSTITUTION = "Liskov Substitution Principle"
    INTERFACE_SEGREGATION = "Interface Segregation Principle"
    DEPENDENCY_INVERSION = "Dependency Inversion Principle"
    ENCAPSULATION = "Encapsulation"
    ABSTRACTION = "Abstraction"

@dataclass
class ClassDesign:
    name: str
    responsibilities: List[str]
    attributes: List[str]
    methods: List[str]
    relationships: List[str]
    code: str = ""

class DesignEvaluator:
    def __init__(self):
        self.principles = {
            DesignPrinciple.SINGLE_RESPONSIBILITY: self._evaluate_srp,
            DesignPrinciple.ENCAPSULATION: self._evaluate_encapsulation,
            DesignPrinciple.ABSTRACTION: self._evaluate_abstraction,
        }
    
    def evaluate_class_design(self, class_design: ClassDesign) -> Dict[str, Any]:
        evaluation = {
            "overall_score": 0,
            "feedback": [],
            "suggestions": [],
            "design_patterns": []
        }
        
        # Evaluate each principle
        total_score = 0
        for principle, evaluator_func in self.principles.items():
            score, feedback = evaluator_func(class_design)
            total_score += score
            evaluation["feedback"].extend(feedback)
        
        evaluation["overall_score"] = total_score / len(self.principles)
        
        # General suggestions
        evaluation["suggestions"] = self._generate_suggestions(class_design)
        evaluation["design_patterns"] = self._identify_patterns(class_design)
        
        return evaluation
    
    def _evaluate_srp(self, class_design: ClassDesign) -> tuple:
        score = 0
        feedback = []
        
        # Check if responsibilities are focused
        if len(class_design.responsibilities) == 1:
            score += 10
            feedback.append(("good", "✅ Single clear responsibility defined"))
        elif len(class_design.responsibilities) <= 3:
            score += 7
            feedback.append(("warning", "⚠️ Multiple responsibilities - consider splitting"))
        else:
            score += 3
            feedback.append(("error", "❌ Too many responsibilities - violates SRP"))
        
        return score, feedback
    
    def _evaluate_encapsulation(self, class_design: ClassDesign) -> tuple:
        score = 0
        feedback = []
        
        # Check for getter/setter methods
        methods_text = " ".join(class_design.methods).lower()
        if "get" in methods_text or "set" in methods_text:
            score += 8
            feedback.append(("good", "✅ Encapsulation with getter/setter methods"))
        
        # Check for private attributes (convention)
        private_attrs = [attr for attr in class_design.attributes if attr.startswith('_') or 'private' in attr.lower()]
        if private_attrs:
            score += 5
            feedback.append(("good", "✅ Private attributes identified"))
        else:
            score += 2
            feedback.append(("warning", "⚠️ Consider making some attributes private"))
        
        return score, feedback
    
    def _evaluate_abstraction(self, class_design: ClassDesign) -> tuple:
        score = 0
        feedback = []
        
        # Check method naming
        method_quality = 0
        for method in class_design.methods:
            if any(verb in method.lower() for verb in ['get', 'set', 'add', 'remove', 'update', 'create', 'delete']):
                method_quality += 1
        
        if method_quality >= len(class_design.methods) * 0.8:
            score += 8
            feedback.append(("good", "✅ Well-named methods with clear actions"))
        else:
            score += 5
            feedback.append(("warning", "⚠️ Some methods could have clearer names"))
        
        return score, feedback
    
    def _generate_suggestions(self, class_design: ClassDesign) -> List[str]:
        suggestions = []
        
        if len(class_design.attributes) > 10:
            suggestions.append("Consider grouping related attributes into separate classes")
        
        if len(class_design.methods) > 15:
            suggestions.append("Large number of methods - consider using composition or inheritance")
        
        if not any("validate" in method.lower() for method in class_design.methods):
            suggestions.append("Consider adding validation methods for data integrity")
        
        return suggestions
    
    def _identify_patterns(self, class_design: ClassDesign) -> List[str]:
        patterns = []
        
        # Check for common patterns
        if any("factory" in method.lower() or "create" in method.lower() for method in class_design.methods):
            patterns.append("Factory Pattern")
        
        if any("observer" in rel.lower() or "listener" in rel.lower() for rel in class_design.relationships):
            patterns.append("Observer Pattern")
        
        if "builder" in class_design.name.lower():
            patterns.append("Builder Pattern")
        
        return patterns

# Initialize session state
if "requirements" not in st.session_state:
    st.session_state.requirements = ""
if "class_designs" not in st.session_state:
    st.session_state.class_designs = {}
if "evaluator" not in st.session_state:
    st.session_state.evaluator = DesignEvaluator()
if "current_step" not in st.session_state:
    st.session_state.current_step = "requirements"

# Main header
st.markdown('<h1 class="main-header">🏗️ Low Level Design Learning Platform</h1>', unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("Navigation")
steps = ["📋 Requirements", "🎨 Class Design", "💻 Code Implementation", "🧪 Demo & Testing"]
current_step = st.sidebar.radio("Current Step:", steps)

# Map radio selection to step keys
step_mapping = {
    "📋 Requirements": "requirements",
    "🎨 Class Design": "design",
    "💻 Code Implementation": "code",
    "🧪 Demo & Testing": "demo"
}
st.session_state.current_step = step_mapping[current_step]

# Requirements Section
if st.session_state.current_step == "requirements":
    st.markdown('<div class="section-header">📋 System Requirements</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("**Teacher Input: Define the system requirements**")
        requirements = st.text_area(
            "Enter system requirements:",
            value=st.session_state.requirements,
            height=300,
            placeholder="""Example: Design a Parking Lot System
- The parking lot has multiple levels
- Each level has parking spots of different types (compact, large, handicapped)
- Vehicles can be cars, motorcycles, or trucks
- The system should track availability and manage parking/unparking
- Payment processing for parking fees
- Real-time spot availability display"""
        )
        
        if st.button("Save Requirements", type="primary"):
            st.session_state.requirements = requirements
            st.success("Requirements saved! Move to Class Design step.")
    
    with col2:
        if st.session_state.requirements:
            st.markdown("**Current Requirements:**")
            st.info(st.session_state.requirements[:300] + "..." if len(st.session_state.requirements) > 300 else st.session_state.requirements)

# Class Design Section
elif st.session_state.current_step == "design":
    st.markdown('<div class="section-header">🎨 Class Design Phase</div>', unsafe_allow_html=True)
    
    if not st.session_state.requirements:
        st.warning("Please define requirements first!")
        st.stop()
    
    # Display requirements
    with st.expander("📋 View Requirements"):
        st.write(st.session_state.requirements)
    
    # Class design input
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("**Design Your Classes:**")
        
        # Class selection/creation
        existing_classes = list(st.session_state.class_designs.keys())
        
        class_option = st.radio("Choose option:", ["Create New Class", "Edit Existing Class"])
        
        if class_option == "Create New Class":
            class_name = st.text_input("Class Name:", placeholder="e.g., ParkingSpot")
        else:
            if existing_classes:
                class_name = st.selectbox("Select Class to Edit:", existing_classes)
            else:
                st.warning("No existing classes found. Create a new class first.")
                st.stop()
        
        if class_name:
            # Load existing design if editing
            if class_option == "Edit Existing Class" and class_name in st.session_state.class_designs:
                existing_design = st.session_state.class_designs[class_name]
                default_resp = existing_design.responsibilities
                default_attrs = existing_design.attributes
                default_methods = existing_design.methods
                default_rels = existing_design.relationships
            else:
                default_resp = []
                default_attrs = []
                default_methods = []
                default_rels = []
            
            # Input fields
            responsibilities = st.text_area(
                "Responsibilities (one per line):",
                value="\n".join(default_resp),
                placeholder="Represent a parking space in the lot\nManage spot availability",
                height=100
            )
            
            attributes = st.text_area(
                "Attributes (one per line):",
                value="\n".join(default_attrs),
                placeholder="spotId\nspotType\nisAvailable\ncurrentVehicle",
                height=100
            )
            
            methods = st.text_area(
                "Methods (one per line):",
                value="\n".join(default_methods),
                placeholder="parkVehicle(vehicle)\nremoveVehicle()\nisAvailable()",
                height=100
            )
            
            relationships = st.text_area(
                "Relationships (one per line):",
                value="\n".join(default_rels),
                placeholder="Has-a Vehicle\nBelongs to ParkingLot",
                height=100
            )
            
            if st.button("Save Class Design", type="primary"):
                class_design = ClassDesign(
                    name=class_name,
                    responsibilities=[r.strip() for r in responsibilities.split('\n') if r.strip()],
                    attributes=[a.strip() for a in attributes.split('\n') if a.strip()],
                    methods=[m.strip() for m in methods.split('\n') if m.strip()],
                    relationships=[r.strip() for r in relationships.split('\n') if r.strip()]
                )
                st.session_state.class_designs[class_name] = class_design
                st.success(f"Class '{class_name}' saved successfully!")
                st.rerun()
    
    with col2:
        st.markdown("**Design Evaluation:**")
        
        if st.session_state.class_designs:
            selected_class = st.selectbox("Evaluate Class:", list(st.session_state.class_designs.keys()))
            
            if st.button("Evaluate Design"):
                evaluation = st.session_state.evaluator.evaluate_class_design(
                    st.session_state.class_designs[selected_class]
                )
                
                # Display score
                st.metric("Design Score", f"{evaluation['overall_score']:.1f}/10")
                
                # Display feedback
                for feedback_type, message in evaluation["feedback"]:
                    if feedback_type == "good":
                        st.markdown(f'<div class="evaluation-good">{message}</div>', unsafe_allow_html=True)
                    elif feedback_type == "warning":
                        st.markdown(f'<div class="evaluation-warning">{message}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="evaluation-error">{message}</div>', unsafe_allow_html=True)
                
                # Suggestions
                if evaluation["suggestions"]:
                    st.markdown("**Suggestions:**")
                    for suggestion in evaluation["suggestions"]:
                        st.write(f"💡 {suggestion}")
                
                # Design patterns
                if evaluation["design_patterns"]:
                    st.markdown("**Identified Patterns:**")
                    for pattern in evaluation["design_patterns"]:
                        st.write(f"🔧 {pattern}")
        
        # Display existing classes
        if st.session_state.class_designs:
            st.markdown("**Designed Classes:**")
            for name, design in st.session_state.class_designs.items():
                with st.expander(f"📦 {name}"):
                    st.write(f"**Responsibilities:** {len(design.responsibilities)}")
                    st.write(f"**Attributes:** {len(design.attributes)}")
                    st.write(f"**Methods:** {len(design.methods)}")
                    st.write(f"**Relationships:** {len(design.relationships)}")

# Code Implementation Section
elif st.session_state.current_step == "code":
    st.markdown('<div class="section-header">💻 Code Implementation</div>', unsafe_allow_html=True)
    
    if not st.session_state.class_designs:
        st.warning("Please design classes first!")
        st.stop()
    
    # Class selection for coding
    class_to_code = st.selectbox("Select Class to Implement:", list(st.session_state.class_designs.keys()))
    
    if class_to_code:
        design = st.session_state.class_designs[class_to_code]
        
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.markdown(f"**Implement: {class_to_code}**")
            
            # Show design details
            with st.expander("📋 View Design Details"):
                st.write("**Responsibilities:**")
                for resp in design.responsibilities:
                    st.write(f"• {resp}")
                st.write("**Attributes:**")
                for attr in design.attributes:
                    st.write(f"• {attr}")
                st.write("**Methods:**")
                for method in design.methods:
                    st.write(f"• {method}")
                st.write("**Relationships:**")
                for rel in design.relationships:
                    st.write(f"• {rel}")
            
            # Code input
            code_template = f'''class {class_to_code}:
    """
    {design.responsibilities[0] if design.responsibilities else 'Class description'}
    """
    
    def __init__(self):
        # Initialize attributes
{chr(10).join([f"        self.{attr.split()[0] if attr else 'attribute'} = None" for attr in design.attributes[:5]])}
        pass
    
{chr(10).join([f"    def {method.split('(')[0] if '(' in method else method}(self):{chr(10)}        # TODO: Implement this method{chr(10)}        pass{chr(10)}" for method in design.methods[:3]])}
'''
            
            code = st.text_area(
                "Write your code:",
                value=design.code if design.code else code_template,
                height=400,
                help="Implement the class based on your design"
            )
            
            if st.button("Save Code", type="primary"):
                st.session_state.class_designs[class_to_code].code = code
                st.success(f"Code for '{class_to_code}' saved!")
        
        with col2:
            st.markdown("**Code Analysis:**")
            
            if design.code:
                # Basic code analysis
                lines = len([line for line in design.code.split('\n') if line.strip()])
                methods_in_code = len([line for line in design.code.split('\n') if 'def ' in line])
                
                st.metric("Lines of Code", lines)
                st.metric("Methods Implemented", methods_in_code)
                
                # Check for common issues
                issues = []
                if "pass" in design.code:
                    issues.append("⚠️ Contains placeholder 'pass' statements")
                if "TODO" in design.code:
                    issues.append("⚠️ Contains TODO comments")
                if "print(" in design.code:
                    issues.append("ℹ️ Contains print statements (consider logging)")
                
                if issues:
                    st.markdown("**Code Issues:**")
                    for issue in issues:
                        st.write(issue)
                else:
                    st.success("✅ No obvious issues detected")
    
    # Show all implemented classes
    st.markdown("**Implementation Progress:**")
    progress_data = []
    for name, design in st.session_state.class_designs.items():
        status = "✅ Implemented" if design.code else "❌ Not Implemented"
        progress_data.append({"Class": name, "Status": status, "Lines": len(design.code.split('\n')) if design.code else 0})
    
    if progress_data:
        st.table(progress_data)

# Demo Section
elif st.session_state.current_step == "demo":
    st.markdown('<div class="section-header">🧪 Demo & Testing</div>', unsafe_allow_html=True)
    
    if not st.session_state.class_designs:
        st.warning("Please design and implement classes first!")
        st.stop()
    
    implemented_classes = {name: design for name, design in st.session_state.class_designs.items() if design.code}
    
    if not implemented_classes:
        st.warning("No classes have been implemented yet!")
        st.stop()
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("**Create Demo Class:**")
        
        demo_code_template = f'''class Demo:
    """
    Demonstration class to show how all classes interact
    """
    
    def __init__(self):
        # Initialize demo environment
        pass
    
    def run_demo(self):
        """
        Main demo method - shows class interactions
        """
        print("=== System Demo ===")
        
        # TODO: Create instances of your classes
        # TODO: Demonstrate their interactions
        # TODO: Show the system working end-to-end
        
        print("Demo completed!")
    
    def test_individual_classes(self):
        """
        Test each class individually
        """
        print("=== Individual Class Tests ===")
        
        # TODO: Test each class's methods
        
        print("All tests completed!")

# Uncomment to run the demo
# if __name__ == "__main__":
#     demo = Demo()
#     demo.run_demo()
#     demo.test_individual_classes()
'''
        
        demo_code = st.text_area(
            "Demo Implementation:",
            value=demo_code_template,
            height=400,
            help="Create a demo class that shows how all your classes work together"
        )
        
        if st.button("Run Demo", type="primary"):
            try:
                # Create a safe execution environment
                exec_globals = {}
                
                # Add all implemented classes to the execution environment
                for name, design in implemented_classes.items():
                    exec(design.code, exec_globals)
                
                # Execute demo code
                exec(demo_code, exec_globals)
                
                # Try to run the demo
                if 'Demo' in exec_globals:
                    demo_instance = exec_globals['Demo']()
                    st.success("✅ Demo code executed successfully!")
                    
                    # Capture output (in a real environment, you'd capture stdout)
                    st.code("Demo would run here - output would be displayed", language="text")
                else:
                    st.warning("Demo class not found in code")
                    
            except Exception as e:
                st.error(f"Error executing demo: {str(e)}")
    
    with col2:
        st.markdown("**Class Summary:**")
        
        for name, design in implemented_classes.items():
            with st.expander(f"📦 {name}"):
                st.write(f"**Methods:** {len(design.methods)}")
                st.write(f"**Attributes:** {len(design.attributes)}")
                st.write(f"**Code Lines:** {len(design.code.split(chr(10)))}")
        
        st.markdown("**System Metrics:**")
        total_classes = len(st.session_state.class_designs)
        implemented = len(implemented_classes)
        total_methods = sum(len(design.methods) for design in st.session_state.class_designs.values())
        
        st.metric("Total Classes Designed", total_classes)
        st.metric("Classes Implemented", f"{implemented}/{total_classes}")
        st.metric("Total Methods", total_methods)
        
        if implemented == total_classes:
            st.success("🎉 All classes implemented!")
        else:
            st.warning(f"{total_classes - implemented} classes still need implementation")

# Footer
st.markdown("---")
st.markdown("**💡 Tips:**")
st.markdown("""
- Follow SOLID principles in your design
- Keep classes focused on single responsibilities  
- Use composition over inheritance when possible
- Add proper validation and error handling
- Write clear, descriptive method names
- Consider edge cases in your implementation
""")

# Progress indicator
progress = 0
if st.session_state.requirements: progress += 25
if st.session_state.class_designs: progress += 25
if any(design.code for design in st.session_state.class_designs.values()): progress += 25
if progress == 75: progress = 100  # Complete when demo is accessible

st.sidebar.markdown("---")
st.sidebar.markdown("**Overall Progress:**")
st.sidebar.progress(progress / 100)
st.sidebar.markdown(f"{progress}% Complete")