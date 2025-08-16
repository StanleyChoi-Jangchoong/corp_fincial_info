package com.opendart.financial.service;

import com.opendart.financial.entity.Corporation;
import com.opendart.financial.repository.CorporationRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 기업 정보 서비스
 */
@Service
public class CorporationService {
    
    @Autowired
    private CorporationRepository corporationRepository;
    
    /**
     * 회사명으로 검색
     */
    public List<Corporation> searchByCompanyName(String companyName) {
        if (companyName == null || companyName.trim().isEmpty()) {
            return List.of();
        }
        return corporationRepository.findByCorpNameOrEngNameContaining(companyName.trim());
    }
    
    /**
     * 기업 코드로 조회
     */
    public Corporation getByCorpCode(String corpCode) {
        return corporationRepository.findById(corpCode).orElse(null);
    }
    
    /**
     * 주식 코드로 검색
     */
    public List<Corporation> searchByStockCode(String stockCode) {
        if (stockCode == null || stockCode.trim().isEmpty()) {
            return List.of();
        }
        return corporationRepository.findByStockCode(stockCode.trim());
    }
    
    /**
     * 모든 기업 조회 (페이징 필요시 추후 구현)
     */
    public List<Corporation> getAllCorporations() {
        return corporationRepository.findAll();
    }
    
    /**
     * 기업 정보 저장
     */
    public Corporation saveCorporation(Corporation corporation) {
        return corporationRepository.save(corporation);
    }
    
    /**
     * 총 기업 수 조회
     */
    public long getTotalCount() {
        return corporationRepository.count();
    }
}
