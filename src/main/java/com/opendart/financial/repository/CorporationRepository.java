package com.opendart.financial.repository;

import com.opendart.financial.entity.Corporation;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * 기업 정보 레포지토리
 */
@Repository
public interface CorporationRepository extends JpaRepository<Corporation, String> {
    
    /**
     * 회사명으로 검색 (부분 일치)
     */
    @Query("SELECT c FROM Corporation c WHERE c.corpName LIKE %:corpName% ORDER BY c.corpName")
    List<Corporation> findByCorpNameContaining(@Param("corpName") String corpName);
    
    /**
     * 회사명 또는 영문 회사명으로 검색 (부분 일치)
     */
    @Query("SELECT c FROM Corporation c WHERE c.corpName LIKE %:searchTerm% OR c.corpEngName LIKE %:searchTerm% ORDER BY c.corpName")
    List<Corporation> findByCorpNameOrEngNameContaining(@Param("searchTerm") String searchTerm);
    
    /**
     * 주식 코드로 검색
     */
    List<Corporation> findByStockCode(String stockCode);
    
    /**
     * 회사명으로 정확히 일치하는 기업 검색
     */
    Corporation findByCorpName(String corpName);
}
