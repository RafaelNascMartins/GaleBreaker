extends SceneTree

func _init() -> void:
    var words := ["BABUIN", "TOPHIA", "VOLT", "IGNIS", "KAZE", "PASSIVO", "DEFENDE ALTO", "DEFENDE BAIXO", "PULA", "IA", "SIM", "NÃO", "TREINO", "LUTADOR", "ADVERSÁRIO", "COMPORTAMENTO", "EXIBIR HITBOXES", "INICIAR TREINO", "ESC VOLTAR", "áàâãéêíóôõúüç ÁÀÂÃÉÊÍÓÔÕÚÜÇ 0123456789"]
    var result := {"engine": Engine.get_version_info().string, "passed": true, "fonts": []}
    for path in ["res://fonts/StardosStencil-Bold.ttf", "res://fonts/PortaoStencil-Desgastado.fnt"]:
        var font := load(path) as Font
        if font == null:
            push_error("Font load failed: " + path)
            quit(1)
            return
        var missing: Array[String] = []
        for text in words:
            for c in text:
                if not font.has_char(c.unicode_at(0)) and c not in missing:
                    missing.append(c)
            var size := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, 64)
            if size.x <= 0:
                push_error("Invalid text metrics: " + text)
                quit(1)
                return
        if not missing.is_empty():
            push_error("Missing glyphs in " + path + ": " + str(missing))
            quit(1)
            return
        result.fonts.append({"path": path, "words_tested": words.size(), "missing": missing, "ascent_64": font.get_ascent(64), "height_64": font.get_height(64)})
    var out := FileAccess.open("res://validation-godot.json", FileAccess.WRITE)
    out.store_string(JSON.stringify(result, "  "))
    print(JSON.stringify(result))
    quit(0)
