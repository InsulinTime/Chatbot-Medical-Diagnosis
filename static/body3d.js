// 3D Body Visualization with Three.js
class Body3DMapper {
    constructor() {
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.bodyModel = null;
        this.selectedRegions = new Set();
        this.rotation = 0;
        this.isFrontView = true;
        
        this.init();
    }
    
    init() {
        const container = document.getElementById('canvas3d');
        const width = container.clientWidth;
        const height = 500;
        
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0xf0f0f0);
        
        this.camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
        this.camera.position.z = 5;
        
        this.renderer = new THREE.WebGLRenderer({ 
            canvas: container,
            antialias: true 
        });
        this.renderer.setSize(width, height);
        
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        this.scene.add(ambientLight);
        
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.4);
        directionalLight.position.set(0, 1, 1);
        this.scene.add(directionalLight);
        
        this.createBodyModel();
        
        this.setupInteraction();
        
        this.animate();
    }
    
    createBodyModel() {
        const bodyGroup = new THREE.Group();
        
        // Materials
        const skinMaterial = new THREE.MeshPhongMaterial({ 
            color: 0xffdbac,
            shininess: 30
        });
        
        const highlightMaterial = new THREE.MeshPhongMaterial({ 
            color: 0xff6b6b,
            transparent: true,
            opacity: 0.5
        });
        
        // Head
        const headGeometry = new THREE.SphereGeometry(0.5, 32, 32);
        const head = new THREE.Mesh(headGeometry, skinMaterial);
        head.position.y = 2;
        head.userData = { region: 'head' };
        bodyGroup.add(head);
        
        const torsoGeometry = new THREE.BoxGeometry(1.5, 2, 0.8);
        const torso = new THREE.Mesh(torsoGeometry, skinMaterial);
        torso.position.y = 0.5;
        torso.userData = { region: 'chest' };
        bodyGroup.add(torso);
        
        const abdomenGeometry = new THREE.BoxGeometry(1.4, 1.5, 0.8);
        const abdomen = new THREE.Mesh(abdomenGeometry, skinMaterial);
        abdomen.position.y = -0.75;
        abdomen.userData = { region: 'abdomen' };
        bodyGroup.add(abdomen);
        
        const armGeometry = new THREE.CylinderGeometry(0.15, 0.15, 2);
        
        const leftArm = new THREE.Mesh(armGeometry, skinMaterial);
        leftArm.position.set(-1, 0.5, 0);
        leftArm.userData = { region: 'arms' };
        bodyGroup.add(leftArm);
        
        const rightArm = new THREE.Mesh(armGeometry, skinMaterial);
        rightArm.position.set(1, 0.5, 0);
        rightArm.userData = { region: 'arms' };
        bodyGroup.add(rightArm);
        
        const legGeometry = new THREE.CylinderGeometry(0.2, 0.2, 2.5);
        
        const leftLeg = new THREE.Mesh(legGeometry, skinMaterial);
        leftLeg.position.set(-0.4, -2.5, 0);
        leftLeg.userData = { region: 'legs' };
        bodyGroup.add(leftLeg);
        
        const rightLeg = new THREE.Mesh(legGeometry, skinMaterial);
        rightLeg.position.set(0.4, -2.5, 0);
        rightLeg.userData = { region: 'legs' };
        bodyGroup.add(rightLeg);
        
        this.bodyModel = bodyGroup;
        this.scene.add(this.bodyModel);
    }
    
    setupInteraction() {
        const canvas = this.renderer.domElement;
        const raycaster = new THREE.Raycaster();
        const mouse = new THREE.Vector2();
        
        canvas.addEventListener('click', (event) => {
            const rect = canvas.getBoundingClientRect();
            mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
            mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
            
            raycaster.setFromCamera(mouse, this.camera);
            const intersects = raycaster.intersectObjects(this.bodyModel.children);
            
            if (intersects.length > 0) {
                const clickedPart = intersects[0].object;
                const region = clickedPart.userData.region;
                
                if (region) {
                    this.handleBodyPartClick(region, clickedPart);
                }
            }
        });
        
        document.querySelectorAll('.body-region').forEach(region => {
            region.addEventListener('click', (e) => {
                const bodyRegion = e.target.dataset.region;
                this.handleBodyPartClick(bodyRegion);
                e.target.classList.toggle('selected');
            });
        });
    }
    
    handleBodyPartClick(region, mesh = null) {
        if (this.selectedRegions.has(region)) {
            this.selectedRegions.delete(region);
            if (mesh) {
                mesh.material = new THREE.MeshPhongMaterial({ 
                    color: 0xffdbac,
                    shininess: 30
                });
            }
        } else {
            this.selectedRegions.add(region);
            if (mesh) {
                mesh.material = new THREE.MeshPhongMaterial({ 
                    color: 0xff6b6b,
                    transparent: true,
                    opacity: 0.7
                });
            }
        }
        
        this.showSymptomSelector(region);
    }
    
    showSymptomSelector(region) {
        const overlay = document.getElementById('symptomOverlay');
        
        const symptoms = {
            head: ['Headache', 'Dizziness', 'Vision problems', 'Ear pain', 'Fever'],
            chest: ['Chest pain', 'Shortness of breath', 'Cough', 'Palpitations'],
            abdomen: ['Stomach pain', 'Nausea', 'Vomiting', 'Bloating', 'Diarrhea'],
            arms: ['Arm pain', 'Weakness', 'Numbness', 'Swelling', 'Tingling'],
            legs: ['Leg pain', 'Cramping', 'Swelling', 'Weakness', 'Numbness'],
            back: ['Back pain', 'Stiffness', 'Shooting pain', 'Numbness']
        };
        
        const regionSymptoms = symptoms[region] || [];
        
        overlay.innerHTML = `
            <h4>${region.charAt(0).toUpperCase() + region.slice(1)} Symptoms</h4>
            <div class="symptom-checkboxes">
                ${regionSymptoms.map(symptom => `
                    <label style="display: block; margin: 5px 0;">
                        <input type="checkbox" value="${symptom}" data-region="${region}">
                        ${symptom}
                    </label>
                `).join('')}
            </div>
            <button onclick="submitBodySymptoms('${region}')" 
                    style="margin-top: 10px; padding: 8px 16px; background: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer;">
                Analyze Symptoms
            </button>
            <button onclick="document.getElementById('symptomOverlay').style.display='none'" 
                    style="margin-left: 5px; padding: 8px 16px; background: #f44336; color: white; border: none; border-radius: 5px; cursor: pointer;">
                Close
            </button>
        `;
        
        overlay.style.display = 'block';
        overlay.style.top = '50%';
        overlay.style.left = '50%';
        overlay.style.transform = 'translate(-50%, -50%)';
    }
    
    animate() {
        requestAnimationFrame(() => this.animate());
        
        if (this.bodyModel) {
            this.bodyModel.rotation.y = this.rotation;
        }
        
        this.renderer.render(this.scene, this.camera);
    }
}

let body3D;
document.addEventListener('DOMContentLoaded', () => {
    body3D = new Body3DMapper();
});

function rotateBody(direction) {
    if (direction === 'left') {
        body3D.rotation -= 0.5;
    } else {
        body3D.rotation += 0.5;
    }
}

function toggleView() {
    body3D.isFrontView = !body3D.isFrontView;
    body3D.rotation = body3D.isFrontView ? 0 : Math.PI;
}

function resetView() {
    body3D.rotation = 0;
    body3D.selectedRegions.clear();
    document.querySelectorAll('.body-region').forEach(r => r.classList.remove('selected'));
}

async function submitBodySymptoms(region) {
    const checkboxes = document.querySelectorAll(`input[data-region="${region}"]:checked`);
    const symptoms = Array.from(checkboxes).map(cb => cb.value);
    
    if (symptoms.length === 0) {
        alert('Please select at least one symptom');
        return;
    }
    
    try {
        const response = await fetch('/analyze_body_region', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                region: region,
                symptoms: symptoms,
                session_id: sessionStorage.getItem('session_id') || 'default'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            if (window.parent && window.parent.addMessage) {
                window.parent.addMessage(
                    `Analysis for ${region} symptoms:\n` +
                    `Possible conditions: ${data.possible_conditions.join(', ')}\n` +
                    `Urgency: ${data.urgent ? 'HIGH - Seek immediate care' : 'Moderate - Schedule clinic visit'}`,
                    'receive'
                );
            }
            
            document.getElementById('symptomOverlay').innerHTML = `
                <h4>Analysis Complete</h4>
                <p><strong>Region:</strong> ${region}</p>
                <p><strong>Urgency:</strong> ${data.urgent ? '🚨 HIGH' : '⚠️ Moderate'}</p>
                <p><strong>Recommendation:</strong> ${data.recommendation}</p>
                <button onclick="document.getElementById('symptomOverlay').style.display='none'">Close</button>
            `;
        }
    } catch (error) {
        console.error('Error submitting symptoms:', error);
        alert('Error analyzing symptoms. Please try again.');
    }
}