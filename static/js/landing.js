/**
 * SAMANITO LANDING PAGE - OPERATIONAL EXCELLENCE LOGIC (2026 EDITION)
 */

document.addEventListener("DOMContentLoaded", () => {
    // 1. App Showcase Toggle (Full Screen, Mobile, Combined View Switcher)
    const btnFullscreen = document.getElementById("showcase-btn-fullscreen");
    const btnMobile = document.getElementById("showcase-btn-mobile");
    const btnCombined = document.getElementById("showcase-btn-combined");
    const viewFullscreen = document.getElementById("showcase-view-fullscreen");
    const viewMobile = document.getElementById("showcase-view-mobile");
    const viewCombined = document.getElementById("showcase-view-combined");

    const deactivateAllViews = () => {
        [btnFullscreen, btnMobile, btnCombined].forEach(btn => btn && btn.classList.remove("active"));
        [viewFullscreen, viewMobile, viewCombined].forEach(view => view && view.classList.add("d-none"));
    };

    if (btnFullscreen && viewFullscreen) {
        btnFullscreen.addEventListener("click", () => {
            deactivateAllViews();
            btnFullscreen.classList.add("active");
            viewFullscreen.classList.remove("d-none");
        });
    }

    if (btnMobile && viewMobile) {
        btnMobile.addEventListener("click", () => {
            deactivateAllViews();
            btnMobile.classList.add("active");
            viewMobile.classList.remove("d-none");
        });
    }

    if (btnCombined && viewCombined) {
        btnCombined.addEventListener("click", () => {
            deactivateAllViews();
            btnCombined.classList.add("active");
            viewCombined.classList.remove("d-none");
        });
    }

    // 2. Calculadora de Eficiencia Operativa (Ahorro de Tiempo y Reducción de Errores)
    const animalSlider = document.getElementById("roi-animal-slider");
    const animalCountDisplay = document.getElementById("roi-animal-count");
    const hoursValDisplay = document.getElementById("roi-hours-val");
    const accuracyValDisplay = document.getElementById("roi-accuracy-val");

    if (animalSlider && animalCountDisplay) {
        const calculateOperations = () => {
            const count = parseInt(animalSlider.value, 10);
            animalCountDisplay.textContent = count.toLocaleString("es-ES");

            const hoursSaved = Math.round(count * 0.24);
            const recordsProcessed = Math.round(count * 6.5);

            if (hoursValDisplay) {
                hoursValDisplay.textContent = hoursSaved + " hrs / mes";
            }
            if (accuracyValDisplay) {
                accuracyValDisplay.textContent = recordsProcessed.toLocaleString("es-ES") + " registros / mes";
            }
        };

        animalSlider.addEventListener("input", calculateOperations);
        calculateOperations();
    }

    // 3. Simulador Interactivo de Asistente Operativo Veti IA
    const promptChips = document.querySelectorAll(".prompt-preset-chip");
    const userMsgBubble = document.getElementById("veti-demo-user-msg");
    const vetiResponseText = document.getElementById("veti-demo-response-text");
    const vetiRecBox = document.getElementById("veti-demo-rec-box");

    const presetData = {
        "lactancia": {
            user: "Veti, ¿cuál fue el pesaje total del ordeño de hoy y qué vacas registraron caídas?",
            response: "El ordeño de hoy sumó <strong class='text-warning'>1,480 Litros</strong>. Registré que la <strong class='text-warning'>Vaca #104</strong> bajó 4.5 L por segundo día consecutivo.",
            rec: "📋 <strong class='text-success'>Alerta Operativa:</strong> Agendar chequeo veterinario en establo para Vaca #104."
        },
        "rotacion": {
            user: "Veti, ¿cuál es el plan de rotación de potreros recomendado para mañana?",
            response: "El <strong class='text-warning'>Potrero 5 (Estrella)</strong> cumplió 28 días de descanso forrajero con excelente rebrote de biomasa.",
            rec: "🌿 <strong class='text-success'>Rotación Sugerida:</strong> Trasladar el Lote A de ordeño al Potrero 5 a las 6:00 AM."
        },
        "sanidad": {
            user: "Veti, ¿qué vacunas o tratamientos sanitarios vencen esta semana?",
            response: "Hay <strong class='text-warning'>18 novillas</strong> pendientes por refuerzo de Aftosa y <strong class='text-warning'>4 vacas</strong> en período de secado.",
            rec: "💉 <strong class='text-success'>Recordatorio Sanitario:</strong> Revisa el lote de vacunación agendado para este jueves."
        }
    };

    promptChips.forEach(chip => {
        chip.addEventListener("click", () => {
            promptChips.forEach(c => c.classList.remove("active"));
            chip.classList.add("active");

            const presetKey = chip.getAttribute("data-preset");
            const data = presetData[presetKey];

            if (data && userMsgBubble && vetiResponseText && vetiRecBox) {
                userMsgBubble.innerHTML = `"${data.user}"`;
                vetiResponseText.innerHTML = data.response;
                vetiRecBox.innerHTML = data.rec;
            }
        });
    });

    // 4. Desplazamiento Suave
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener("click", function(e) {
            const targetId = this.getAttribute("href");
            if (targetId && targetId !== "#") {
                const targetEl = document.querySelector(targetId);
                if (targetEl) {
                    e.preventDefault();
                    const navHeight = document.querySelector(".navbar-glass")?.offsetHeight || 80;
                    const pos = targetEl.getBoundingClientRect().top + window.pageYOffset - navHeight;
                    window.scrollTo({ top: pos, behavior: "smooth" });
                }
            }
        });
    });
});

// Slider de estadísticas del hero (móvil): flechas ◀ ▶
(function () {
    const slider = document.getElementById('heroStatsSlider');
    const prev = document.getElementById('heroStatsPrev');
    const next = document.getElementById('heroStatsNext');
    if (!slider || !prev || !next) return;
    const step = (dir) => {
        const w = slider.clientWidth + 12; // ancho de tarjeta + gap
        const max = slider.scrollWidth - slider.clientWidth;
        let target = slider.scrollLeft + dir * w;
        if (target > max + 5) target = 0;          // vuelve al inicio
        if (target < -5) target = max;             // va al final
        slider.scrollTo({ left: target, behavior: 'smooth' });
    };
    prev.addEventListener('click', () => step(-1));
    next.addEventListener('click', () => step(1));
})();
