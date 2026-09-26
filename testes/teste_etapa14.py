"""
Teste da Etapa 14: Responsividade móvel.
Valida media queries, touch gestures e otimizacoes para mobile.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def teste_media_queries_768():
    """Testa media queries para tablets (≤768px)."""
    print("\n--- Media queries tablet (768px) ---")
    
    with open("interface/assets/style.css", 'r', encoding='utf-8') as f:
        css = f.read()
    
    assert "@media (max-width: 768px)" in css, "Deve ter media query para 768px"
    print("  X media query 768px presente")
    
    assert "font-size: 13px" in css, "Deve reduzir font-size para mobile"
    print("  X tamanhos ajustados para tablet")
    
    assert "--widget-w: 100%" in css, "Deve usar width 100% em mobile"
    print("  X layout full-width em mobile")

def teste_media_queries_480():
    """Testa media queries para smartphones (≤480px)."""
    print("\n--- Media queries smartphone (480px) ---")
    
    with open("interface/assets/style.css", 'r', encoding='utf-8') as f:
        css = f.read()
    
    assert "@media (max-width: 480px)" in css, "Deve ter media query para 480px"
    print("  X media query 480px presente")
    
    assert "flex-direction: column" in css, "Deve usar flex-column em 480px"
    print("  X layout vertical em smartphone")
    
    assert "height: 40px" in css or "height: 44px" in css, "Deve ajustar altura de topbar"
    print("  X controles otimizados para dedo")

def teste_viewport_meta_tag():
    """Testa viewport meta tag no HTML."""
    print("\n--- Viewport meta tag ---")
    
    with open("interface/index.html", 'r', encoding='utf-8') as f:
        html = f.read()
    
    assert 'viewport-fit=cover' in html, "Deve ter viewport-fit=cover para notch"
    print("  X viewport-fit=cover para notch")
    
    assert 'user-scalable=no' in html, "Deve desabilitar zoom do usuario"
    print("  X zoom desabilitado para melhor UX")
    
    assert 'apple-mobile-web-app-capable' in html, "Deve ser webapp compativel"
    print("  X compatibilidade com Apple mobile webapp")
    
    assert 'theme-color' in html, "Deve definir cor do tema"
    print("  X theme-color definida")

def teste_touch_gestures():
    """Testa suporte para touch gestures."""
    print("\n--- Touch gestures ---")
    
    with open("interface/assets/script.js", 'r', encoding='utf-8') as f:
        js = f.read()
    
    assert "class TouchGestureDetector" in js, "Deve ter classe para touch gestures"
    print("  X TouchGestureDetector presente")
    
    assert "touchstart" in js, "Deve escutar touchstart"
    print("  X evento touchstart implementado")
    
    assert "touchend" in js, "Deve escutar touchend"
    print("  X evento touchend implementado")
    
    assert "onSwipeLeft" in js, "Deve ter handler para swipe esquerda"
    print("  X swipe esquerda implementado")
    
    assert "onSwipeRight" in js, "Deve ter handler para swipe direita"
    print("  X swipe direita implementado")

def teste_otimizacoes_mobile():
    """Testa otimizacoes para mobile."""
    print("\n--- Otimizacoes para mobile ---")
    
    with open("interface/assets/script.js", 'r', encoding='utf-8') as f:
        js = f.read()
    
    assert "otimizarParaMobile" in js, "Deve ter funcao de otimizacao"
    print("  X funcao otimizarParaMobile presente")
    
    assert "style.overflow" in js, "Deve controlar overflow em mobile"
    print("  X overflow controlado")
    
    assert "MutationObserver" in js, "Deve usar MutationObserver para auto-scroll"
    print("  X auto-scroll do historico implementado")
    
    assert "inicializarTouchGestures" in js, "Deve inicializar touch gestures"
    print("  X inicializacao de touch gestures")

def teste_css_input_height():
    """Testa tamanho de inputs para mobile."""
    print("\n--- Tamanho de inputs para mobile ---")
    
    with open("interface/assets/style.css", 'r', encoding='utf-8') as f:
        css = f.read()
    
    assert "--input-h: 48px" in css, "Deve ter altura minima de input em tablet"
    print("  X input height 48px em tablet (touch-friendly)")
    
    assert "--input-h: 44px" in css, "Deve ter altura em smartphone"
    print("  X input height 44px em smartphone")

def teste_font_sizes_mobile():
    """Testa ajuste de font-sizes para mobile."""
    print("\n--- Font sizes para mobile ---")
    
    with open("interface/assets/style.css", 'r', encoding='utf-8') as f:
        css = f.read()
    
    # Procura por reducoes de font-size em media queries
    tablet_section = css[css.find("@media (max-width: 768px)"):css.find("@media (max-width: 480px)")]
    
    assert "font-size: 13px" in tablet_section, "Deve reduzir font para 13px em tablet"
    print("  X font-size reduzido em tablet")
    
    smartphone_section = css[css.find("@media (max-width: 480px)"):css.find("@media (max-height: 600px)")]
    
    assert "font-size: 12px" in smartphone_section or "font-size: 11px" in smartphone_section, "Deve reduzir mais em smartphone"
    print("  X font-size reduzido em smartphone")

def teste_landscape_orientation():
    """Testa media query para landscape."""
    print("\n--- Orientacao landscape ---")
    
    with open("interface/assets/style.css", 'r', encoding='utf-8') as f:
        css = f.read()
    
    assert "@media (orientation: landscape)" in css, "Deve ter media query para landscape"
    print("  X media query landscape presente")
    
    landscape_section = css[css.find("@media (orientation: landscape)"):len(css)]
    assert "height" in landscape_section or "max-height" in landscape_section, "Deve ajustar altura em landscape"
    print("  X altura otimizada para landscape")

def teste_button_sizes():
    """Testa tamanhos de botoes para mobile."""
    print("\n--- Tamanho de botoes para mobile ---")
    
    with open("interface/assets/style.css", 'r', encoding='utf-8') as f:
        css = f.read()
    
    tablet_section = css[css.find("@media (max-width: 768px)"):css.find("@media (max-width: 480px)")]
    
    assert "width: 44px" in tablet_section, "Botoes devem ter minimo 44px"
    print("  X botoes touch-friendly (44px minimo)")
    
    smartphone_section = css[css.find("@media (max-width: 480px)"):css.find("@media (max-height: 600px)")]
    assert "padding" in smartphone_section, "Deve ajustar padding de botoes"
    print("  X padding de botoes ajustado")

def teste_side_panel_mobile():
    """Testa ocultacao de side panel em mobile."""
    print("\n--- Side panel em mobile ---")
    
    with open("interface/assets/style.css", 'r', encoding='utf-8') as f:
        css = f.read()
    
    tablet_section = css[css.find("@media (max-width: 768px)"):css.find("@media (max-width: 480px)")]
    
    assert ".side-panel {" in tablet_section and "display: none" in tablet_section, "Side panel deve sumir em mobile"
    print("  X side panel oculto em tablet")
    
    assert ".app.fullscreen-mode .side-panel" in tablet_section, "Deve aparecer em fullscreen"
    print("  X side panel visivel em fullscreen mobile")

def main():
    print("=" * 68)
    print("TESTE DA ETAPA 14: Responsividade Móvel")
    print("=" * 68)
    
    try:
        teste_media_queries_768()
        teste_media_queries_480()
        teste_viewport_meta_tag()
        teste_touch_gestures()
        teste_otimizacoes_mobile()
        teste_css_input_height()
        teste_font_sizes_mobile()
        teste_landscape_orientation()
        teste_button_sizes()
        teste_side_panel_mobile()
        
        print("\n" + "=" * 68)
        print("OK TODOS OS TESTES DA ETAPA 14 PASSARAM!")
        print("Responsividade móvel validada.")
        print("=" * 68)
        return 0
        
    except AssertionError as e:
        print(f"\nERRO: {e}")
        return 1
    except Exception as e:
        print(f"\nERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
