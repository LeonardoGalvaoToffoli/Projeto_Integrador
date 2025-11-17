package br.com.integrador.service_busca_java.controller;

import br.com.integrador.service_busca_java.dto.SearchRequestDto;
import br.com.integrador.service_busca_java.dto.SearchResponseDto;
import br.com.integrador.service_busca_java.service.SearchService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/")
public class SearchController {

    @Autowired
    private SearchService searchService;

    /**
     * Endpoint para ingestão e indexação dos dados de clusterização.
     */
    @PostMapping("/build")
    public ResponseEntity<String> build(@RequestBody Map<String, double[]> centroids) {
        try {
            searchService.buildIndex(centroids);
            return ResponseEntity.ok("Índice construído com sucesso.");
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body("Erro na construção do índice: " + e.getMessage());
        }
    }

    /**
     * Endpoint para busca de similaridade.
     */
    @PostMapping("/search")
    public ResponseEntity<SearchResponseDto> search(@RequestBody SearchRequestDto request) {
        try {
            String closestCluster = searchService.findClosestCluster(request.getImageVector());
            return ResponseEntity.ok(new SearchResponseDto(closestCluster));
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body(null);
        }
    }
}