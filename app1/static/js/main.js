/* ==========================================================================
   SAMANITO LANDING PAGE JAVASCRIPT - GSAP SCROLLTRIGGER & INTERACTUACIÓN UI
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
    // 1. Reading Progress Bar
    const progressBar = document.getElementById("reading-progress-bar");
    window.addEventListener("scroll", () => {
        const totalHeight = document.documentElement.scrollHeight - window.innerHeight;
        const progress = (window.scrollY / totalHeight) * 100;
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
        }
    });

    // 2. Register GSAP ScrollTrigger Plugin
    if (typeof gsap !== "undefined" && typeof ScrollTrigger !== "undefined") {
        gsap.registerPlugin(ScrollTrigger);

        // Hero Content Fade In & Scale
        gsap.from(".hero-content", {
            duration: 1.2,
            y: 40,
            opacity: 0,
            ease: "power3.out"
        });

        // Parallax Effect on Hero Background
        gsap.to(".hero-section", {
            scrollTrigger: {
                trigger: ".hero-section",
                start: "top top",
                end: "bottom top",
                scrub: true
            },
            backgroundPositionY: "50%"
        });

        // Stagger Reveal for Feature Cards
        gsap.from(".reveal-card", {
            scrollTrigger: {
                trigger: "#caracteristicas",
                start: "top 80%"
            },
            y: 50,
            opacity: 0,
            duration: 0.8,
            stagger: 0.15,
            ease: "power2.out"
        });

        // Reveal for TL;DR Box
        gsap.from(".tldr-box", {
            scrollTrigger: {
                trigger: ".tldr-box",
                start: "top 85%"
            },
            y: 30,
            opacity: 0,
            duration: 0.8,
            ease: "power2.out"
        });

        // Counter Animations for Metrics
        const counters = document.querySelectorAll(".counter-value");
        counters.forEach(counter => {
            const target = +counter.getAttribute("data-target");
            gsap.to(counter, {
                scrollTrigger: {
                    trigger: counter,
                    start: "top 85%"
                },
                innerText: target,
                duration: 2,
                snap: { innerText: 1 },
                ease: "power1.out"
            });
        });
    }

    // 3. Social Share Functionality
    const shareBtns = document.querySelectorAll("[data-share]");
    shareBtns.forEach(btn => {
        btn.addEventListener("click", (e) => {
            e.preventDefault();
            const platform = btn.getAttribute("data-share");
            const url = encodeURIComponent(window.location.href);
            const text = encodeURIComponent("Conoce Samanito: Software Ganadero de Gestión Integral, Finanzas y Producción Lechera.");

            let shareUrl = "";
            if (platform === "whatsapp") {
                shareUrl = `https://api.whatsapp.com/send?text=${text}%20${url}`;
            } else if (platform === "x") {
                shareUrl = `https://twitter.com/intent/tweet?text=${text}&url=${url}`;
            } else if (platform === "linkedin") {
                shareUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${url}`;
            } else if (platform === "copy") {
                navigator.clipboard.writeText(window.location.href);
                alert("¡Enlace copiado al portapapeles!");
                return;
            }

            if (shareUrl) {
                window.open(shareUrl, "_blank", "width=600,height=400");
            }
        });
    });
});
