document.addEventListener('DOMContentLoaded', () => {
  const loginButton = document.getElementById('login-button');
  const rocketElement = document.getElementById('single-rocket');
  const svgElement = document.querySelector('svg');
  const starsElement = document.getElementById('stars');
  const rocketsContainer = document.getElementById('rockets-container');
  const mainContent = document.querySelector('.mein_content');
  const meinContainer = mainContent.querySelector('.mein_container');
  const contentSvg = mainContent.querySelector('#content');
  const body = document.body;

  let isDragging = false;
  let offsetX, offsetY;

  const startY = -225;
  const intermediateY = -125;
  const finalY = loginButton.getBoundingClientRect().bottom + rocketElement.offsetHeight + 50;
  const startX = window.innerWidth / 2;
  const targetX = loginButton.getBoundingClientRect().left + loginButton.offsetWidth / 2 - rocketElement.offsetWidth / 2;
  const finalRotationAngle = -90;

  let animationProgress = 0;
  const animationDurationBeforeButton = 5000;
  const animationDurationAfterButton = 5000;

  rocketElement.style.top = `${startY}%`;
  rocketElement.style.left = `${startX - rocketElement.offsetWidth / 2}px`;
  rocketElement.style.transform = `translateX(-50%) rotate(180deg)`;

  function animateRocket() {
    const currentTime = performance.now();
    let progress;
    let currentY;
    let currentX;
    let currentRotation;

    if (currentTime < 5000) {
      progress = Math.min(1, currentTime / animationDurationBeforeButton);
      currentY = startY + (intermediateY - startY) * progress;
      currentX = startX;
      currentRotation = 180;
    } else {
      const elapsedTimeAfterButton = currentTime - 5000;
      progress = Math.min(1, elapsedTimeAfterButton / animationDurationAfterButton);
      currentY = intermediateY + (finalY - intermediateY) * progress;
      currentX = startX + (targetX - startX) * progress;
      currentRotation = 180 + (finalRotationAngle - 180) * progress;
    }

    rocketElement.style.top = `${currentY}%`;
    rocketElement.style.left = `${currentX - rocketElement.offsetWidth / 2}px`;
    rocketElement.style.transform = `translateX(-50%) rotate(${currentRotation}deg)`;

    if (currentTime < 10000) {
      requestAnimationFrame(animateRocket);
    } else {
      rocketElement.style.pointerEvents = 'auto';
    }
  }

  setTimeout(() => {
    loginButton.style.opacity = 1;
    loginButton.style.transform = 'translateY(0)';
    animateRocket();
  }, 5000);

  rocketElement.addEventListener('mousedown', (e) => startDrag(e));
  rocketElement.addEventListener('touchstart', (e) => startDrag(e));

  function startDrag(event) {
    isDragging = true;
    rocketElement.style.cursor = 'grabbing';
    rocketElement.style.animation = 'none';
    let clientX, clientY;
    if (event.clientX !== undefined) {
      clientX = event.clientX;
      clientY = event.clientY;
    } else if (event.touches && event.touches.length > 0) {
      clientX = event.touches[0].clientX;
      clientY = event.touches[0].clientY;
    } else {
      return;
    }
    offsetX = clientX - rocketElement.getBoundingClientRect().left;
    offsetY = clientY - rocketElement.getBoundingClientRect().top;
  }

  document.addEventListener('mousemove', (e) => dragRocket(e));
  document.addEventListener('touchmove', (e) => dragRocket(e));

  function dragRocket(event) {
    if (!isDragging) return;
    let clientX, clientY;
    if (event.clientX !== undefined) {
      clientX = event.clientX;
      clientY = event.clientY;
    } else if (event.touches && event.touches.length > 0) {
      clientX = event.touches[0].clientX;
      clientY = event.touches[0].clientY;
    } else {
      return;
    }
    rocketElement.style.left = `${clientX - offsetX}px`;
    rocketElement.style.top = `${clientY - offsetY}px`;
  }

  document.addEventListener('mouseup', stopDrag);
  document.addEventListener('touchend', stopDrag);
  document.addEventListener('mouseleave', stopDrag);
  document.addEventListener('touchcancel', stopDrag);

  function stopDrag() {
    isDragging = false;
    rocketElement.style.cursor = 'grab';
  }

  function fadeOutElements() {
    rocketElement.style.transition = 'opacity 1s ease-in-out';
    rocketElement.style.opacity = 0;

    svgElement.style.transition = 'opacity 1s ease-in-out';
    svgElement.style.opacity = 0;

    loginButton.style.transition = 'opacity 1s ease-in-out';
    loginButton.style.opacity = 0;

    if (starsElement) {
      starsElement.style.transition = 'opacity 1s ease-in-out';
      starsElement.style.opacity = 0;
    }

    if (rocketsContainer) {
      rocketsContainer.style.transition = 'opacity 1s ease-in-out';
      rocketsContainer.style.opacity = 0;
    }

    meinContainer.style.position = 'fixed';
    meinContainer.style.top = '20px';
    meinContainer.style.left = '20px';
    meinContainer.style.right = '20px';
    meinContainer.style.bottom = '20px';
    meinContainer.style.border = '2px solid red';
    meinContainer.style.borderRadius = '10px';
    meinContainer.style.display = 'flex';
    meinContainer.style.flexDirection = 'column';
    meinContainer.style.alignItems = 'center';
    meinContainer.style.paddingTop = '40px';

    contentSvg.style.position = 'absolute';
    contentSvg.style.width = '300%'; // Например, уменьшаем ширину до 50% от родительского контейнера
    contentSvg.style.height = 'auto'; // Сохраняем пропорции высоты
    contentSvg.style.top = '8%';
    contentSvg.style.left = '50%';
    contentSvg.style.transform = 'translateX(-50%) translateY(-50%)';

    mainContent.style.display = 'block';
    mainContent.style.opacity = 0;
    mainContent.style.transition = 'opacity 1s ease-in-out';
    setTimeout(() => {
      mainContent.style.opacity = 1;
      body.style.backgroundImage = "url('fonts.png')"; // Устанавливаем фоновое изображение
      body.style.backgroundSize = "cover";
      body.style.backgroundPosition = "center";

      rocketElement.style.display = 'none';
      svgElement.style.display = 'none';
      loginButton.style.display = 'none';
      if (starsElement) {
        starsElement.style.display = 'none';
      }
      if (rocketsContainer) {
        rocketsContainer.style.display = 'none';
      }
    }, 1000);
  }

  loginButton.addEventListener('click', fadeOutElements);
});
