package com.opendart.financial.controller;

import com.opendart.financial.entity.Corporation;
import com.opendart.financial.service.CorporationService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 기업 정보 REST API 컨트롤러
 */
@RestController
@RequestMapping("/api/corporations")
@CrossOrigin(origins = "*") // CORS 허용
public class CorporationController {
    
    @Autowired
    private CorporationService corporationService;
    
    /**
     * 회사명으로 검색
     */
    @GetMapping("/search")
    public ResponseEntity<List<Corporation>> searchCorporations(
            @RequestParam("q") String query) {
        
        List<Corporation> corporations = corporationService.searchByCompanyName(query);
        return ResponseEntity.ok(corporations);
    }
    
    /**
     * 기업 코드로 상세 조회
     */
    @GetMapping("/{corpCode}")
    public ResponseEntity<Corporation> getCorporation(@PathVariable String corpCode) {
        Corporation corporation = corporationService.getByCorpCode(corpCode);
        if (corporation != null) {
            return ResponseEntity.ok(corporation);
        } else {
            return ResponseEntity.notFound().build();
        }
    }
    
    /**
     * 주식 코드로 검색
     */
    @GetMapping("/stock/{stockCode}")
    public ResponseEntity<List<Corporation>> getCorporationByStockCode(@PathVariable String stockCode) {
        List<Corporation> corporations = corporationService.searchByStockCode(stockCode);
        return ResponseEntity.ok(corporations);
    }
    
    /**
     * 전체 기업 수 조회
     */
    @GetMapping("/count")
    public ResponseEntity<Long> getTotalCount() {
        long count = corporationService.getTotalCount();
        return ResponseEntity.ok(count);
    }
    
    /**
     * 상태 확인용 엔드포인트
     */
    @GetMapping("/health")
    public ResponseEntity<String> health() {
        return ResponseEntity.ok("API 서버가 정상적으로 동작 중입니다.");
    }
}
